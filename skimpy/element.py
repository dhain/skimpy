class ElementType(type):
    def __new__(cls, name, bases, dct):
        children = dct['children'] = set()
        for base in bases:
            if isinstance(base, ElementType):
                children |= base.children
        for key in dct:
            value = dct[key]
            if not isinstance(value, ElementType):
                continue
            value = dct[key] = value._mk_subclass()
            value.name = key
            children.add(key)
        return type.__new__(cls, name, bases, dct)

    def __get__(self, obj, cls):
        attr = '_%s__parent' % (self.__name__,)
        bound = self._mk_subclass()
        setattr(bound, attr, cls)
        if obj is not None:
            bound = bound()
            setattr(bound, attr, obj)
        return bound

    def _mk_subclass(self):
        return type(self.__name__, (self,), {})


class Element(object):
    __metaclass__ = ElementType
    value = None

    class parent(object):
        def __get__(self, obj, cls):
            attr = '_%s__parent' % (cls.__name__,)
            try:
                if obj is None:
                    return cls.__dict__[attr]
                else:
                    return obj.__dict__.get(attr, cls.__dict__[attr])
            except (KeyError, AttributeError):
                raise AttributeError(
                    "%r object has no attribute 'parent'" % (cls.__name__,))
    parent = parent()

    class path(object):
        def __get__(self, obj, cls):
            path = []
            el = cls
            while True:
                try:
                    path.append(el.name)
                    el = el.parent
                except AttributeError:
                    break
            path.reverse()
            return '.'.join(path)
    path = path()

    def __getattribute__(self, name):
        value = super(Element, self).__getattribute__(name)
        if (
            not name.startswith('__')
            and name not in self.__dict__
            and isinstance(value, Element)
        ):
            self.__dict__[name] = value
        return value

    @classmethod
    def from_flat(cls, flat):
        root = cls()
        els = [root]
        while els:
            el = els.pop()
            els.extend(getattr(el, attr) for attr in el.children)
            path = el.path
            if path in flat:
                el.value = flat[path]
        return root
