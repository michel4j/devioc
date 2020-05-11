# DevIOC
Simple Python Device IOC Support for EPICS

DevIOC is a package which enables python based EPICS IOC Soft Device support all within python. It
allows you to define the IOC database model in a manner similar to Django Database models, and to use
the model to develop dynamic, IOC servers.

To use the full capabilities, it is is highly recommended to use a GObject compatible main loop, such as the
one provided by `PyGObject` or even better, the GObject compatible `Twisted` reactor.

Detailed documentation is available at https://michel4j.github.io/devioc/
