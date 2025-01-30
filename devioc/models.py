import multiprocessing
import os
import platform
import shutil
import subprocess
import sys
import time
from collections.abc import Iterable
from enum import EnumMeta
from pathlib import Path
from typing import Tuple, Union, Dict

import gepics

from . import log

ENUM_KEYS = [
    'ZR', 'ON', 'TW', 'TH', 'FR', 'FV', 'SX', 'SV',
    'EI', 'NI', 'TE', 'EL', 'TV', 'TT', 'FT', 'FF'
]

logger = log.get_module_logger(__name__)


class RecordType(type):
    """Record MetaClass"""

    def __new__(cls, name, bases, attrs):
        # update fields
        fields = {}
        fields.update(getattr(bases[0], 'fields', {}))
        fields.update(attrs.get('fields'))
        attrs['fields'] = fields

        return super(RecordType, cls).__new__(cls, name, bases, attrs)


class Record(object, metaclass=RecordType):
    """
    Base class for all record types. Do not use directly.

    :param name: Record name (str)
    :keyword desc: Description (str). Sets the DESC field
    :keyword *: additional keyword arguments
    """

    record = 'ai'
    fields = {
        'DESC': '{desc}',
    }

    def __init__(self, name, **kwargs):
        kwargs.update(name=name, desc=kwargs.get("desc", "None"))
        kw = {k: v for k, v in kwargs.items() if v is not None}
        self.options = {}
        self.options.update(kw)
        self.options['record'] = self.record
        self.instance_fields = {}
        self.instance_fields.update(self.fields)

    def __str__(self):
        template = '\n'.join(
            ['record({record}, "$(device):{name}") {{'] +
            [f'  field({k}, {v!r})' for k, v in self.instance_fields.items()] +
            ['}}', '']
        )
        return template.format(**self.options)

    def add_field(self, key, value):
        """
        Add a database record field

        :param key: field name
        :param value: field value
        :return:
        """
        self.instance_fields[key] = value

    def del_field(self, key):
        """
        Delete a database record field

        :param key: field name
        """
        if key in self.instance_fields:
            del self.instance_fields[key]

    def get(self, *args, **kwargs):
        ...

    def put(self, *args, **kwargs):
        ...


class Enum(Record):
    """
    Enum record type

    :param name: Record name (str)
    :keyword choices: list/tuple of strings corresponding to the choice names, values will be 0-index integers.
    :keyword default: default value of the record, 0 by default. Sets the VAL field
    :keyword *: Extra keyword arguments
    """

    record = 'mbbo'
    fields = {
        'VAL': '{default}',
        'OUT': '{out}'
    }

    def __init__(self, name, **kwargs):
        kwargs.update(
            choices=kwargs.get("choices", ["OFF", "ON"]),
            out=kwargs.get("out", ""),
            default=kwargs.get("default", 0)
        )
        super(Enum, self).__init__(name, **kwargs)
        if isinstance(self.options['choices'], EnumMeta):
            choice_pairs = [(e.name.replace('_', ' '), e.value) for e in self.options['choices']]
        elif isinstance(self.options['choices'], Iterable):
            choice_pairs = [(c, i) for i, c in enumerate(self.options['choices'])]
        else:
            choice_pairs = []
        for i in range(len(choice_pairs)):
            name, value = choice_pairs[i]
            key = ENUM_KEYS[i]
            self.add_field(f'{key}VL', f"{value}")
            self.add_field(f'{key}ST', name)


class BinaryOutput(Record):
    """
    Binary record type for converting between integers and bits

    :param name: Record name (str)
    :keyword out: Output link specification. Sets the OUT field
    :keyword shift: shift value by this number of bits to the right. Sets the SHFT field
    :keyword default: default value of the record, 0 by default. Sets the VAL field
    :keyword *: Extra keyword arguments
    """

    record = 'mbboDirect'
    fields = {
        'VAL': '{default}',
        'OUT': '{out}',
        'SHFT': '{shift}',
    }

    def __init__(self, name, **kwargs):
        kwargs.update(
            out=kwargs.get("out", ""),
            default=kwargs.get("default", 0),
            shift=kwargs.get("shift", 0)
        )
        super(BinaryOutput, self).__init__(name, **kwargs)


class BinaryInput(Record):
    """
    Binary record type for converting between integers and bits

    :param name: Record name (str)
    :keyword inp: Input link. Sets the INP field
    :keyword shift: shift value by this number of bits to the right. Sets the SHFT field
    :keyword default: default value of the record, 0 by default. Sets the VAL field
    :keyword *: Extra keyword arguments
    """
    record = 'mbbiDirect'
    fields = {
        'VAL': '{default}',
        'INP': '{inp}',
        'SHFT': '{shift}',
    }

    def __init__(self, name, **kwargs):
        kwargs.update(
            inp=kwargs.get("inp", ""),
            default=kwargs.get("default", 0),
            shift=kwargs.get("shift", 0)
        )
        super(BinaryInput, self).__init__(name, **kwargs)


class Toggle(Record):
    """
    Toggle field corresponding to a binary out record.

    :param name: Record name (str)
    :keyword high: Duration to keep high before returning to zero. Sets the HIGH field.
    :keyword zname: string value when zero. Sets the ZNAM field
    :keyword oname: string value when high. Sets the ONAM field
    :keyword *: Extra keyword arguments
    """
    record = 'bo'
    fields = {
        'ZNAM': '{zname}',
        'ONAM': '{oname}',
        'HIGH': '{high}'
    }

    def __init__(self, name, **kwargs):
        kwargs.update(
            high=kwargs.get("high", 0.1),
            zname=kwargs.get("zname", name),
            oname=kwargs.get("oname", "")
        )
        super(Toggle, self).__init__(name, **kwargs)


class String(Record):
    """
    String record. Uses standard string record, or character array depending on length
    """

    record = 'stringout'
    fields = {
        'VAL': '{default}'
    }

    def __init__(self, name, max_length: Union[int, str] = 20, default: str = " ", **kwargs):
        """
        :param name: Record name (str)
        :param max_length:
            maximum number of characters expected. Char Array records will be used for fields bigger than 40 characters, in
            which case the NELM and FTVL field will be set.
        :param default:  default value, empty string by default
        :param *: Extra keyword arguments

        """
        kwargs.update(
            max_length=max_length,
            default=default
        )
        super(String, self).__init__(name, **kwargs)
        if self.options['max_length'] > 40:
            self.options['record'] = 'waveform'
            self.add_field('NELM', self.options['max_length'])
            self.add_field('FTVL', 'CHAR')
            self.del_field('VAL')


class Integer(Record):
    """
    Integer Record.

    :param name: Record Name.
    :param max_val: Maximum value permitted (float), default (no limit). Sets the DRVH and HOPR fields
    :param min_val: Minimum value permitted (float), default (no limit). Sets the DRVL and LOPR fields
    :param default: default value, default (0.0). Sets the VAL field
    :param units:  engineering units (str), default empty string. Sets the EGU field
    :param kwargs: Extra keyword arguments
    """
    record = 'longout'
    fields = {
        'HOPR': '{max_val}',
        'LOPR': '{min_val}',
        'DRVH': '{max_val}',
        'DRVL': '{min_val}',
        'VAL': '{default}',
        'EGU': '{units}',
    }

    def __init__(
            self,
            name,
            max_val: Union[int, str] = 0.,
            min_val: Union[int, str] = 0.,
            default: Union[int, str] = 0.,
            units: str = '',
            **kwargs
    ):
        kwargs.update(
            max_val=max_val,
            min_val=min_val,
            default=default,
            units=units,
        )
        super(Integer, self).__init__(name, **kwargs)


class Float(Record):
    """
    Float Record.

    :param name: Record Name.
    :param max_val: Maximum value permitted (float), default (no limit). Sets the DRVH and HOPR fields
    :param min_val: Minimum value permitted (float), default (no limit). Sets the DRVL and LOPR fields
    :param prec: number of decimal places, default (4). Sets the PREC field
    :param default: default value, default (0.0). Sets the VAL field
    :param units:  engineering units (str), default empty string. Sets the EGU field
    :param kwargs: Extra keyword arguments
    """

    record = 'ao'
    fields = {
        'DRVH': '{max_val}',
        'DRVL': '{min_val}',
        'HOPR': '{max_val}',
        'LOPR': '{min_val}',
        'PREC': '{prec}',
        'EGU': '{units}',
        'VAL': '{default}'
    }

    def __init__(
            self,
            name,
            max_val: Union[float, str] = 0.,
            min_val: Union[float, str] = 0.,
            default: Union[float, str] = 0.,
            prec: Union[float, str] = 4,
            units: str = '',
            **kwargs
    ):
        kwargs.update(
            max_val=max_val,
            min_val=min_val,
            default=default,
            prec=prec,
            units=units,
        )
        super(Float, self).__init__(name, **kwargs)


class Calc(Record):
    """
    Calc Record

    :param name: Record name
    :param scan: scan parameter, default (0 ie passive). Sets the SCAN field
    :param prec: number of decimal places, default (4). Sets the PREC field
    :param calc: Calculation. Sets CALC field
    :param inpa: Input A specification. Sets the INPA field
    :param kwargs: Extra keyword arguments. Any additional database fields required should be specified as lower-case kwargs.
    """

    record = 'calc'
    fields = {
        'CALC': '{calc}',
        'SCAN': '{scan}',
        'PREC': '{prec}',
    }

    def __init__(
            self,
            name: str,
            scan: Union[int,  str] = 0,
            prec: Union[int,  str] = 0,
            calc: str = '',
            **kwargs
    ):
        kwargs.update(
            scan=scan,
            prec=prec,
            calc=calc
        )
        super(Calc, self).__init__(name, **kwargs)
        for c in 'ABCDEFGHIJKL':
            key = f'INP{c}'
            if key.lower() in self.options:
                self.add_field(key, self.options[key.lower()])


class CalcOut(Calc):
    """
    CalcOutput Record
    """

    record = 'calcout'
    fields = {
        'OOPT': '{oopt}',
        'DOPT': '{dopt}',
        'OUT': '{out}',
    }

    def __init__(self, name, out: str = "", oopt: Union[int,  str] = 0, dopt: Union[int, str] = 0, **kwargs):
        """
        :param name: Record name
        :param out: OUT Output specification
        :param oopt: OOPT Output Execute field
        :param dopt: DOPT Output Data field
        :param *: Extra keyword arguments, supports Calc kwargs also.

        """
        kwargs.update(out=out, oopt=oopt, dopt=dopt)
        super(CalcOut, self).__init__(name, **kwargs)


class Array(Record):
    """
    Array Record.

    :param name: Record Name
    :param type: Element type (str or python type), supported types are ['STRING', 'SHORT', 'FLOAT', int, str, float]
    :param length: Number of elements in the array
    :param kwargs: Extra kwargs
    """
    record = 'waveform'
    fields = {
        'NELM': '{length}',
        'FTVL': '{type}',
    }

    def __init__(self, name, type: Union[str, type] = int, length: Union[int, str] = 256, **kwargs):
        kwargs.update(type=type, length=length)
        super(Array, self).__init__(name, **kwargs)
        element_type = self.options['type']
        self.options['type'] = {
            str: 'STRING',
            int: 'LONG',
            float: 'FLOAT',
        }.get(element_type, element_type)


CMD_TEMPLATE = """
## Load record instances
dbLoadRecords("{db_name}.db", "{macros}")
iocInit()
dbl
"""


class ModelType(type):
    def __new__(cls, name, bases, attrs):
        fields = {}
        for k, v in list(attrs.items()):
            if isinstance(v, Record):
                fields[k] = v
                del attrs[k]
        attrs['_fields'] = fields
        return super(ModelType, cls).__new__(cls, name, bases, attrs)


def run_softioc(args, stdin_id, stdout_id):
    """
    Launch EPICS ioc binary


    :param args:
    :param stdin_id: Standard input file descriptor
    :param stdout_id: Standard output file descriptor
    :return:
    """

    if platform.system() == 'Windows':
        # output redirection not needed on Windows
        subprocess.check_call(args)
    else:
        with os.fdopen(stdout_id) as stdout:
            with os.fdopen(stdin_id) as stdin:
                subprocess.check_call(args, stdin=stdin, stdout=stdout)


class Model(object, metaclass=ModelType):
    """
    IOC Database Model

    :param device_name:  Root Name of device this will be available as the $(device) macro within the model
    :param callbacks: Callback handler which provides callback methods for handling events and commands
    :param command: The softIoc command to execute. By default this is 'softIoc' from EPICS base.
    :param macros: additional macros to be used in the database as a dictionary

    Process Variable records will be named *<device_name>:<record_name>*.

    If Callback Handler is not provided, it is assumed that all callbacks are defined within the model itself.
    The expected callback methods must follow the signature:

    .. code-block:: python

        def do_<record_name>(self, pv, value, ioc):
            ...

    which accepts the active record (pv), the changed value (value) and the ioc instance (ioc). If the Model
    is also the callbacks provider, self, and ioc are identical, otherwise ioc is a reference to the database
    model on which the record resides.
    """

    _fields: Dict[str, Record]

    def __init__(self, device_name, callbacks=None, command='softIoc', macros=None):
        self.device_name = device_name
        self.db_name = self.__class__.__name__
        self.callbacks = callbacks or self
        self.ioc_process = None
        self.macros = {'device': self.device_name}
        if isinstance(macros, dict):
            self.macros.update(**macros)
        self.command = command
        self.ready = False
        self.directory = Path(os.getcwd())
        self.connections = {}
        self.db_cache_dir = self.directory / '__dbcache__'
        self._startup()
        self._setup()

    def save_db(self) -> Tuple[Path, Path]:
        """
        Save the database and command files
        :return: Tuple of database and command file paths
        """

        if not self.db_cache_dir.exists():
            self.db_cache_dir.mkdir(parents=True, exist_ok=True)

        db_filename = self.db_cache_dir / f'{self.db_name}.db'
        cmd_filename = self.db_cache_dir / f'{self.db_name}.cmd'
        with open(db_filename, 'w') as db_file:
            for k, v in self._fields.items():
                db_file.write(str(v))

        with open(cmd_filename, 'w') as cmd_file:
            macro_text = ','.join([f'{k}={v}' for k, v in self.macros.items()])
            cmd_file.write(CMD_TEMPLATE.format(macros=macro_text, db_name=self.db_name))

        return db_filename, cmd_filename

    def _startup(self):
        """
        Generate the database and start the IOC application in a separate process
        """

        self.save_db()

        os.chdir(self.db_cache_dir)
        args = [self.command, f'{self.db_name}.cmd']

        self.ioc_process = multiprocessing.Process(
            target=run_softioc,
            args=(args, sys.stdin.fileno(), sys.stdout.fileno()),
        )
        self.ioc_process.daemon = True
        self.ioc_process.start()

    def shutdown(self):
        """
        Shutdown the ioc application
        """

        self.ioc_process.terminate()
        subprocess.check_call('reset', shell=True)
        shutil.rmtree(self.db_cache_dir)
        self.ioc_process.join()

    def connect_callbacks(self, pv, value, name):
        callback = getattr(self.callbacks, name, None)
        pv.disconnect('changed')
        if callback:
            pv.connect('changed', callback, self)
            print('connecting ...', name)

    def _setup(self):
        """
        Set up the ioc records and connect all callbacks
        """
        pending = set()
        for k, f in self._fields.items():
            pv_name = f'{self.device_name}:{f.options["name"]}'
            callback_name = f'do_{k}'.lower()
            pv = gepics.PV(pv_name)
            setattr(self, k, pv)
            callback = getattr(self.callbacks, callback_name, None)
            if callback:
                pv.connect('changed', callback, self)
            pending.add(pv)

        # wait for all PVs to connect
        timeout = time.time() + 5
        while pending and time.time() < timeout:
            time.sleep(0.025)
            pending = {pv for pv in pending if not pv.is_active()}

        self.ready = True
        print('')
