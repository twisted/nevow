# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Minimal amount of code from Twisted's components.py
necessary in order to have Nevow run with only zope.interface.
"""
import types, warnings

from zope.interface.interface import Interface, InterfaceClass
from zope.interface import declarations, adapter

from nevow import util

# Twisted's global adapter registry
globalRegistry = adapter.AdapterRegistry()

def registerAdapter(adapterFactory, origInterface, *interfaceClasses):
    """Register an adapter class.

    An adapter class is expected to implement the given interface, by
    adapting instances implementing 'origInterface'. An adapter class's
    __init__ method should accept one parameter, an instance implementing
    'origInterface'.
    """
    assert interfaceClasses, "You need to pass an Interface"

    # deal with class->interface adapters:
    if not isinstance(origInterface, InterfaceClass):
        origInterface = declarations.implementedBy(origInterface)
        
    for interfaceClass in interfaceClasses:
        globalRegistry.register([origInterface], interfaceClass, '', adapterFactory)

def backwardsCompatImplements(obj):
    pass

def fixClassImplements(obj):
    pass



def getInterfaces(klass):
    """DEPRECATED. Return list of all interfaces the class implements. Or the object provides.

    This is horrible and stupid. Please use zope.interface.providedBy() or implementedBy().
    """
    warnings.warn("getInterfaces should not be used, use providedBy() or implementedBy()", ComponentsDeprecationWarning, stacklevel=2)
    # try to support both classes and instances, giving different behaviour
    # which is HORRIBLE :(
    if isinstance(klass, (type, types.ClassType)):
        fixClassImplements(klass)
        l = list(declarations.implementedBy(klass))
    else:
        fixClassImplements(klass.__class__)
        l = list(declarations.providedBy(klass))
    r = []
    for i in l:
        r.extend(superInterfaces(i))
    return util.uniquify(r)

class Componentized:
    """I am a mixin to allow you to be adapted in various ways persistently.

    I define a list of persistent adapters.  This is to allow adapter classes
    to store system-specific state, and initialized on demand.  The
    getComponent method implements this.  You must also register adapters for
    this class for the interfaces that you wish to pass to getComponent.

    Many other classes and utilities listed here are present in Zope3; this one
    is specific to Twisted.
    """

    def __init__(self):
        self._adapterCache = {}

    def locateAdapterClass(self, klass, interfaceClass, default, registry=None):
        return getAdapterClassWithInheritance(klass, interfaceClass, default)

    def setAdapter(self, interfaceClass, adapterClass):
        self.setComponent(interfaceClass, adapterClass(self))

    def addAdapter(self, adapterClass, ignoreClass=0, registry=None):
        """Utility method that calls addComponent.  I take an adapter class and
        instantiate it with myself as the first argument.

        @return: The adapter instantiated.
        """
        adapt = adapterClass(self)
        self.addComponent(adapt, ignoreClass, registry)
        return adapt

    def setComponent(self, interfaceClass, component):
        """
        """
        if hasattr(component, "__class__"):
            fixClassImplements(component.__class__)
        self._adapterCache[util.qual(interfaceClass)] = component

    def addComponent(self, component, ignoreClass=0, registry=None):
        """
        Add a component to me, for all appropriate interfaces.

        In order to determine which interfaces are appropriate, the component's
        provided interfaces will be scanned.

        If the argument 'ignoreClass' is True, then all interfaces are
        considered appropriate.

        Otherwise, an 'appropriate' interface is one for which its class has
        been registered as an adapter for my class according to the rules of
        getComponent.

        @return: the list of appropriate interfaces
        """
        if hasattr(component, "__class__"):
            fixClassImplements(component.__class__)
        for iface in declarations.providedBy(component):
            if (ignoreClass or
                (self.locateAdapterClass(self.__class__, iface, None, registry)
                 == component.__class__)):
                self._adapterCache[util.qual(iface)] = component
        
    def unsetComponent(self, interfaceClass):
        """Remove my component specified by the given interface class."""
        del self._adapterCache[util.qual(interfaceClass)]

    def removeComponent(self, component):
        """
        Remove the given component from me entirely, for all interfaces for which
        it has been registered.

        @return: a list of the interfaces that were removed.
        """
        if (isinstance(component, types.ClassType) or
            isinstance(component, types.TypeType)):
            warnings.warn("passing interface to removeComponent, you probably want unsetComponent", DeprecationWarning, 1)
            self.unsetComponent(component)
            return [component]
        l = []
        for k, v in self._adapterCache.items():
            if v is component:
                del self._adapterCache[k]
                l.append(reflect.namedObject(k))
        return l
    
    def getComponent(self, interface, registry=None, default=None):
        """Create or retrieve an adapter for the given interface.

        If such an adapter has already been created, retrieve it from the cache
        that this instance keeps of all its adapters.  Adapters created through
        this mechanism may safely store system-specific state.

        If you want to register an adapter that will be created through
        getComponent, but you don't require (or don't want) your adapter to be
        cached and kept alive for the lifetime of this Componentized object,
        set the attribute 'temporaryAdapter' to True on your adapter class.

        If you want to automatically register an adapter for all appropriate
        interfaces (with addComponent), set the attribute 'multiComponent' to
        True on your adapter class.
        """
        registry = getRegistry(registry)
        k = util.qual(interface)
        if self._adapterCache.has_key(k):
            return self._adapterCache[k]
        else:
            adapter = interface.__adapt__(self)
            if hasattr(adapter, "__class__"):
                fixClassImplements(adapter.__class__)
            if adapter is not None and adapter is not _Nothing and not (
                hasattr(adapter, "temporaryAdapter") and
                adapter.temporaryAdapter):
                self._adapterCache[k] = adapter
                if (hasattr(adapter, "multiComponent") and
                    adapter.multiComponent):
                    self.addComponent(adapter)
            return adapter

    def __conform__(self, interface):
        return self.getComponent(interface)
    
class Adapter:
    def __init__(self, original):
        """Set my 'original' attribute to be the object I am adapting.
        """
        self.original = original

    def __conform__(self, interface):
        if hasattr(self.original, "__conform__"):
            return self.original.__conform__(interface)
        return None
        


CannotAdapt = TypeError

__all__ = ['globalRegistry', 'registerAdapter', 'backwardsCompatImplements', 'fixClassImplements',
           'getInterfaces', 'IComponentized', 'Componentized', 'Adapter', 'CannotAdapt']
