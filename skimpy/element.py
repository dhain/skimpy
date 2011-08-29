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
            if key != 'element_type':
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
        value = object.__getattribute__(self, name)
        if (
            not name.startswith('__')
            and name not in self.__dict__
            and isinstance(value, Element)
        ):
            self.__dict__[name] = value
        return value

    def _from_flat(self, flat):
        try:
            self.value = flat[self.path]
        except KeyError:
            pass

    @classmethod
    def from_flat(cls, flat):
        root = cls()
        els = [root]
        while els:
            el = els.pop()
            els.extend(getattr(el, attr) for attr in el.children)
            el._from_flat(flat)
        return root


class List(Element, list):
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

    def _from_flat(self, flat):
        Element._from_flat(self, flat)
        for sub_flat in self._extract_flats(flat):
            self.append(self.element_type.from_flat(sub_flat))

    def __getattribute__(self, name):
        if name == 'element_type':
            search = [self.__class__]
            while search:
                cls = search.pop()
                search.extend(reversed(cls.__bases__))
                if name not in cls.__dict__:
                    continue
                el = cls.__dict__[name]
                return type(el.__name__, (el,), {'name': self.name})
            raise AttributeError
        return Element.__getattribute__(self, name)

    @classmethod
    def of(cls, element):
        dct = dict(element_type=element)
        try:
            dct['name'] = element.name
        except AttributeError:
            pass
        return type(element.__name__, (cls,), dct)
