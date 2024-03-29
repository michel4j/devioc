.. title::  DevIOC - EPICS Soft Device Support With Python

.. image:: static/icon.svg
   :align: center
   :width: 120px


.. toctree::
   :maxdepth: 2
   :caption: Contents:

Overview
========
DevIOC is a package which enables python based EPICS IOC Soft Device support all within python. It
allows you to define the IOC database model in a manner similar to Django Database models, and to use
the model to develop dynamic, IOC servers.

To use the full capabilities, it is is highly recommended to use a GObject compatible main loop, such as the
one provided by `PyGObject` or even better, the GObject compatible `Twisted` reactor.

This library has been used to support very complex network IOC devices with non-trivial communication
protocols. It works!

Getting Started
===============
Before you can use DevIOC, you'll need to install it and its dependencies. We recommend installing it inside a virtual
environment using the following commands on the shell

::

    $ python -m venv devioc
    $ source devioc/bin/activate
    (devioc) $ pip3 install devioc


It is a pure python module, although it requires
`PyGObject <https://pypi.org/project/PyGObject/>`_, `Numpy <https://pypi.org/project/numpy/>`_ and
`Twisted <https://pypi.org/project/Twisted/>`_.

DevIOC Also requires a fully functional `EPICS Base <https://epics.anl.gov/base/index.php>`_ installation. If you haven't so yet,
please build and install EPICS Base. It has been tested with EPICS Base versions 3.14 to 3.16.

Once it is installed, you can run the tests to make sure your system is properly _setup, and all required
dependencies are available.

::

   (devioc) $ python -m unittest -v devioc.tests.test_ioc


Write your first IOC
====================
Your IOC application can be structured at will although we recommend the following directory template

::

   myioc
   ├── bin
   │   ├── app.server   # Command to run IOC Application
   │   └── opi.client   # Command to run Operator Display Application
   ├── opi              # Directory containing Operator Display screens
   └── myioc            # Python package for your IOC Application and all other supporting modules
       ├── __init__.py
       └── ioc.py       # IOC module containing your IOC application


A program is included to create a default IOC project. This can be run within the `devioc` virtual environment as follows

::

   (devioc) $ devioc-startproject myioc

This will create a directory structure similar to the one listed above, except the `opi.client` file which you
will have to create yourself based on your preferred EPICS display manager. The project created as such is
a fully functional example application that you can modify as needed.


Creating the IOC Model
======================
If you are familar with the Django Framework, the IOC model should feel natural. All IOC models should inherit
from **devioc.models.Model** and declare database records using the record types defined in **devioc.models**.

For example:


.. code-block:: python

   from devioc import models

   class MyIOC(models.Model):
       enum = models.Enum('enum', choices=['ZERO', 'ONE', 'TWO'], default=0, desc='Enum Test')
       toggle = models.Toggle('toggle', zname='ON', oname='OFF', desc='Toggle Test')
       sstring = models.String('sstring', max_length=20, desc='Short String Test')
       lstring = models.String('lstring', max_length=512, desc='Long String Test')
       intval = models.Integer('intval', max_val=1000, min_val=-1000, default=0, desc='Int Test')
       floatval = models.Float(
           'floatval', max_val=1e6, min_val=1e-6, default=0.0,
           prec=5, desc='Float Test'
       )
       floatout = models.Float('floatout', desc='Test Float Output')
       intarray = models.Array('intarray', type=int, length=16, desc='Int Array Test')
       floatarray = models.Array('floatarray', type=float, length=16, desc='Float Array Test')
       calc = models.Calc(
           'calc', calc='A+B',
           inpa='$(device):intval CP NMS',
           inpb='$(device):floatval CP NMS',
           desc='Calc Test'
       )

Once the model is defined, it can then be instanciated within the application. For example:

.. code-block:: python

   ioc = MyIOC('MYIOC-001')



.. note::
    In the example above, the `floatarray` field uses a macro substitution variable `$(device)` within its specification.
    By default the first argument passed to the model is used as the device name and will be substituted for `$(device)`
    references.

    Additional macro substitution variables can be used and provided to the model during initialization as key-value pairs
    using the macros keyword argument of the model. In practice, the best way to pass these external variables is to make
    them command-line arguments of the application, and then forward them to the model through the application as
    keyword arguments.


This will create an IOC database with Process variable fields **MYIOC-001:enum, MYIOC-001:toggle, ...** etc, where
the process variable name is generated based on the model name, and the field name.  Once instanciated, the IOC is ready
to be used and alive on the Channel Access network. However, for more responsive applications, it is recommended to
to create an IOC Application as well.


.. autoclass:: devioc.models.Model
   :members:

.. seealso:: `Record Types`_ for detailed documentation about database records.

Creating the IOC Application
============================
The IOC Application manages the IOC database and should provide the logic for the application. This can include
connecting to a device through a serial interface, over the network, handling commands from the model, processing and
generating new values for the database fields, etc. The sky is the limit.

For example, let us create an application which uses the model above and responds to changes to the **MYIOC-001:toggle**
field.

.. code-block:: python

      class MyIOCApp(object):

       def __init__(self, device_name):
           self.ioc = MyIOC(device_name, callbacks=self)

       def do_toggle(self, pv, value, ioc):
           """
           I am called whenever the `toggle` record's value changes
           """
           if value == 1:
               # Command activated, value will return to 0 after some time
               print('Toggle Changed Value', value)
               ioc.enum.put((ioc.enum.get() + 1) % 3, wait=True)  # cycle through values

       def do_enum(self, pv, value, ioc):
           print('New Enum Value', value)

       def shutdown(self):
           # needed for proper IOC shutdown
           self.ioc.shutdown()


This application is initialized with the IOC device name.

Running the IOC Application
===========================
The script **bin/app.server** is responsible for running the IOC Application. An example script is generated by the
**devioc-startproject** command. It can be modified to suit your needs. For example:

.. code-block:: python

   #!/usr/bin/env python
   import os
   import logging
   import sys
   import argparse

   # Twisted boiler-plate code.
   from twisted.internet import gireactor
   gireactor.install()
   from twisted.internet import reactor

   # add the project to the python path and inport it
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   from devioc import log
   from myioc import ioc

   # Setup command line arguments
   parser = argparse.ArgumentParser(description='Run IOC Application')
   parser.add_argument('--verbose', action='store_true', help='Verbose Logging')
   parser.add_argument('--device', type=str, help='Device Name', required=True)


   if __name__== '__main__':
       args = parser.parse_args()
       if args.verbose:
           log.log_to_console(logging.DEBUG)
       else:
           log.log_to_console(logging.INFO)

       # initialize App
       app = ioc.MyIOCApp(args.device)

       # make sure app is properly shutdown
       reactor.addSystemEventTrigger('before', 'shutdown', app.shutdown)

       # run main-loop
       reactor.run()


This example uses the `Twisted <https://pypi.org/project/Twisted/>`_ framework. It is highly recommended to use it too.

The above script is executed to start the application within the `devioc` virtual environment as follows:

::

   (devioc) $ myioc/bin/app.server --device MYIOC-001


Record Types
============

Records are defined within the **devioc.models** module. The following record types
are currently supported:

.. py:currentmodule:: devioc.models

.. autoclass:: Record
.. autoclass:: Enum
.. autoclass:: BinaryInput
.. autoclass:: BinaryOutput
.. autoclass:: Toggle
.. autoclass:: Integer
.. autoclass:: Float
.. autoclass:: String
.. autoclass:: Array
.. autoclass:: Calc
.. autoclass:: CalcOut


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
