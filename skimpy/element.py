class ElementType(type):
    def __new__(cls, name, bases, dct):
        children = dct['children'] = {}
        for key, value in dct.items():
            if not isinstance(value, ElementType):
                continue
            if key != 'element_type':
                del dct[key]
                value = children[key] = value.with_attrs(name=key)
        return type.__new__(cls, name, bases, dct)

    def __getitem__(self, key):
        search = [self]
        while search:
            cls = search.pop()
            search.extend(reversed(cls.__bases__))
            if not isinstance(cls, ElementType) or key not in cls.children:
                continue
            return cls.children[key].with_attrs(parent=self)
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.children[key] = value

    def __iter__(self):
        seen = set()
        search = [self]
        while search:
            cls = search.pop()
            search.extend(cls.__bases__)
            if not isinstance(cls, ElementType):
                continue
            for key in cls.children:
                if key not in seen:
                    seen.add(key)
                    yield key

    def iterkeys(self):
        for key in self:
            yield key

    def keys(self):
        return list(self)

    def itervalues(self):
        for key in self:
            yield self[key]

    def values(self):
        return list(self.itervalues())

    def with_attrs(self, **kw):
        return type.__new__(ElementType, self.__name__, (self,), kw)


class Element(object):
    __metaclass__ = ElementType
    raw_value = None
    value = None
    converter = None
    conversion_error = None

    def __new__(cls, *args, **kw):
        self = object.__new__(cls)
        self.instances = {}
        return self

    def __getitem__(self, key):
        try:
            inst = self.instances[key]
        except KeyError:
            inst = self.instances[key] = self.__class__[key]()
            inst.parent = self
        return inst

    def __setitem__(self, key, value):
        value = value.copy()
        value.parent = self
        self.instances[key] = value

    def __iter__(self):
        return self.__class__.__class__.__iter__(self.__class__)

    def iterkeys(self):
        for key in self:
            yield key

    def itervalues(self):
        for key in self:
            yield self[key]

    def values(self):
        return list(self.itervalues())

    def copy(self):
        copy = type(self)()
        copy.__dict__ = self.__dict__.copy()
        for el in copy.itervalues():
            el.parent = copy
        return copy

    class path(object):
        def __get__(self, obj, cls):
            path = []
            el = cls if obj is None else obj
            while True:
                try:
                    path.append(el.name)
                    el = el.parent
                except AttributeError:
                    break
            path.reverse()
            return '.'.join(path)
    path = path()

    def convert(self, strict=True):
        if self.converter is None:
            self.value = self.raw_value
        else:
            try:
                self.value = self.converter(self.raw_value)
            except Exception, inst:
                if strict:
                    raise
                self.conversion_error = inst

    def _from_flat(self, flat, convert=True, strict=False):
        try:
            self.raw_value = flat[self.path]
        except KeyError:
            pass
        if convert:
            self.convert(strict)

    @classmethod
    def from_flat(cls, flat, convert=True, strict=False):
        root = cls()
        els = [root]
        while els:
            el = els.pop()
            els.extend(el.itervalues())
            el._from_flat(flat, convert, strict)
        return root


class List(list, Element):
    def _extract_sub_items(self, flat):
        path = self.path
        prefix_len = len(path)
        for key, value in flat.iteritems():
            if not (
                key[:prefix_len] == path and
                key[prefix_len:prefix_len + 1] == '-'
            ):
                continue
            sub_key = key[prefix_len + 1:]
            try:
                idx, sub_key = sub_key.split('.', 1)
            except ValueError:
                idx = sub_key
                sub_key = path
            else:
                sub_key = path + '.' + sub_key
            if not idx.isdigit():
                continue
            yield int(idx), sub_key, value

    def _extract_flats(self, flat):
        flats = []
        last_idx = None
        for idx, sub_key, value in sorted(
            self._extract_sub_items(flat),
            key=lambda (idx, sub_key, value): idx
        ):
            if idx != last_idx:
                flats.append({})
                last_idx = idx
            flats[-1][sub_key] = value
        return flats

    def __getattribute__(self, name):
        value = list.__getattribute__(self, name)
        if name == 'element_type':
            value = value.with_attrs(name=self.name)
        return value

    def _from_flat(self, flat, convert=True, strict=False):
        Element._from_flat(self, flat, convert, strict)
        for sub_flat in self._extract_flats(flat):
            self.append(self.element_type.from_flat(
                sub_flat, convert, strict))

    @classmethod
    def of(cls, element):
        dct = dict(element_type=element)
        for name in ('name', 'converter'):
            try:
                dct[name] = getattr(element, name)
            except AttributeError:
                pass
        return cls.with_attrs(**dct)
