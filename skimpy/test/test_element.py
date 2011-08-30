import unittest

from skimpy.element import *


class TestElement(unittest.TestCase):
    def test_getting_nonexistent_child_raises_keyerror(self):
        with self.assertRaises(KeyError):
            Element['bogus']

    def test_get_returns_copy_bound_to_parent(self):
        class A(Element):
            element = Element
        self.assertIsNot(A['element'], Element)
        self.assertIs(A['element'].parent, A)

    def test_get_on_instance_returns_instance_bound_to_parent_instance(self):
        class A(Element):
            element = Element
        a = A()
        self.assertTrue(isinstance(a['element'], Element))
        self.assertIs(a['element'].parent, a)

    def test_subsequent_instance_gets_return_same_instance(self):
        class A(Element):
            element = Element
        a = A()
        self.assertIs(a['element'], a['element'])

    def test_get_works_with_element_subclass(self):
        class MyElement(Element):
            pass
        class A(Element):
            element = MyElement
        self.assertIsNot(A['element'], MyElement)
        self.assertIs(A['element'].parent, A)

    def test_get_works_with_parent_subclass(self):
        class MyElement(Element):
            pass
        class A(Element):
            element = MyElement
        class B(A):
            pass
        self.assertIsNot(B['element'], MyElement)
        self.assertIs(B['element'].parent, B)

    def test_get_returns_correct_element_with_multiple_inheritance(self):
        class MyElement(Element):
            pass
        class A(Element):
            element = MyElement
        class B(Element):
            element = Element
        class C(A, B):
            pass
        self.assertTrue(issubclass(C['element'], MyElement))

    def test_get_works_with_parent_subclass_instance(self):
        class MyElement(Element):
            pass
        class A(Element):
            element = MyElement
        class B(A):
            pass
        b = B()
        self.assertTrue(isinstance(b['element'], MyElement))
        self.assertIs(b['element'].parent, b)

    def test_can_set_name_on_class(self):
        class MyElement(Element):
            name = 'a_name'
        self.assertEqual(MyElement.name, 'a_name')

    def test_can_set_name_on_instance(self):
        class MyElement(Element):
            pass
        el = MyElement()
        el.name = 'a_name'
        self.assertEqual(el.name, 'a_name')

    def test_path(self):
        class E1(Element):
            class E2(Element):
                class E3(Element):
                    pass
        self.assertEqual(E1['E2']['E3'].path, 'E2.E3')

    def test_path_works_when_supplanted(self):
        class E1(Element):
            class E2(Element):
                class E3(Element):
                    pass
        class E4(Element):
            pass
        E4['E3'] = E1['E2']['E3']
        self.assertEqual(E4['E3'].path, 'E3')

    def test_path_works_when_supplanted_on_instance(self):
        class E1(Element):
            class E2(Element):
                class E3(Element):
                    pass
        class E4(Element):
            pass
        e1 = E1()
        e4 = E4()
        e4['E3'] = e1['E2']['E3']
        self.assertIs(e4['E3'].parent, e4)
        self.assertEqual(e4['E3'].path, 'E3')

    def test_path_with_custom_names(self):
        class E1(Element):
            e2 = type('E2', (Element,), {'e3': Element})
        self.assertEqual(E1['e2']['e3'].path, 'e2.e3')

    def test_can_have_no_children(self):
        self.assertEqual(Element.keys(), [])

    def test_iter_yields_child_names(self):
        class E(Element):
            a = Element
            b = Element
            c = Element
        self.assertEqual(set(E), set('a b c'.split()))

    def test_can_iter_on_child(self):
        class E1(Element):
            class E2(Element):
                a = Element
                b = Element
                c = Element
        self.assertEqual(set(E1['E2']), set('a b c'.split()))

    def test_inherits_children_from_superclass(self):
        class E1(Element):
            a = type('E1a', (Element,), {})
        class E2(Element):
            a = type('E2a', (Element,), {})
        class E3(E1, E2):
            b = Element
        self.assertEqual(set(E3), set('a b'.split()))
        self.assertEqual(E3['a'].__name__, 'E1a')

    def test_iter_on_instance_yields_child_names(self):
        class E(Element):
            a = Element
            b = Element
            c = Element
        e = E()
        self.assertEqual(set(e), set('a b c'.split()))

    def test_subclass_can_have_init_args(self):
        class MyElement(Element):
            def __init__(self, arg1):
                pass
        self.assertTrue(isinstance(MyElement(1), MyElement))

    def test_convert_is_strict_by_default(self):
        class MyElement(Element):
            converter = int
        e = MyElement()
        e.raw_value = 'a'
        with self.assertRaises(ValueError):
            e.convert()
        self.assertEqual(e.value, None)

    def test_from_flat(self):
        class MyElement(Element):
            a = Element
            b = Element
            class c(Element):
                a = Element
                b = Element
                c = Element
        e = MyElement.from_flat({
            'a': 1,
            'b': 2,
            'c': 3,
            'c.a': 4,
            'c.b': 5,
        })
        self.assertEqual(e['a'].value, 1)
        self.assertEqual(e['b'].value, 2)
        self.assertEqual(e['c'].value, 3)
        self.assertEqual(e['c']['a'].value, 4)
        self.assertEqual(e['c']['b'].value, 5)
        self.assertEqual(e['c']['c'].value, None)

    def test_from_flat_with_root_name(self):
        class MyElement(Element):
            name = 'root'
            a = Element
            b = Element
            class c(Element):
                a = Element
                b = Element
                c = Element
        e = MyElement.from_flat({
            'root': 0,
            'root.a': 1,
            'root.b': 2,
            'root.c': 3,
            'root.c.a': 4,
            'root.c.b': 5,
        })
        self.assertEqual(e['a'].value, 1)
        self.assertEqual(e['b'].value, 2)
        self.assertEqual(e['c'].value, 3)
        self.assertEqual(e['c']['a'].value, 4)
        self.assertEqual(e['c']['b'].value, 5)
        self.assertEqual(e['c']['c'].value, None)

    def test_converts_data(self):
        class MyElement(Element):
            converter = int
        el = MyElement.from_flat({'': '1'})
        self.assertEqual(el.raw_value, '1')
        self.assertEqual(el.value, 1)

    def test_can_skip_conversion(self):
        class MyElement(Element):
            converter = int
        el = MyElement.from_flat({'': '1'}, convert=False)
        self.assertEqual(el.raw_value, '1')
        self.assertEqual(el.value, None)

    def test_notes_conversion_errors_by_default(self):
        class MyElement(Element):
            converter = int
        el = MyElement.from_flat({'': 'a'})
        self.assertEqual(el.raw_value, 'a')
        self.assertEqual(el.value, None)
        self.assertTrue(isinstance(el.conversion_error, ValueError))

    def test_raises_conversion_errors_when_strict(self):
        class MyElement(Element):
            converter = int
        with self.assertRaises(ValueError):
            el = MyElement.from_flat({'': 'a'}, strict=True)

    def test_flatten(self):
        class MyElement(Element):
            a = Element
            b = Element
            class c(Element):
                a = Element
                b = Element
                c = Element
        flat = {
            'a': 1,
            'b': 2,
            'c': 3,
            'c.a': 4,
            'c.b': 5,
        }
        e = MyElement.from_flat(flat)
        self.assertEqual(e.flatten(), flat)

    def test_flatten_with_root_name(self):
        class MyElement(Element):
            name = 'root'
            a = Element
            b = Element
            class c(Element):
                a = Element
                b = Element
                c = Element
        flat = {
            'root': 0,
            'root.a': 1,
            'root.b': 2,
            'root.c': 3,
            'root.c.a': 4,
            'root.c.b': 5,
        }
        e = MyElement.from_flat(flat)
        self.assertEqual(e.flatten(), flat)

    def test_can_include_empty_values_in_flatten(self):
        class MyElement(Element):
            a = Element
            b = Element
            class c(Element):
                a = Element
                b = Element
                c = Element
        flat = {
            'a': 1,
            'b': 2,
            'c': 3,
            'c.a': 4,
            'c.b': 5,
        }
        e = MyElement.from_flat(flat)
        flat[''] = None
        flat['c.c'] = None
        self.assertEqual(e.flatten(include_empty=True), flat)

    def test_flatten_adapts_by_default(self):
        class MyElement(Element):
            adapter = str
        e = MyElement()
        e.value = 1
        self.assertEqual(e.flatten(), {'': '1'})

    def test_can_skip_adapting(self):
        class MyElement(Element):
            adapter = str
        e = MyElement()
        e.value = 1
        self.assertEqual(e.flatten(adapt=False), {'': 1})

    def test_validate_with_no_validators(self):
        e = Element()
        self.assertTrue(e.is_valid())

    def test_can_be_invalid(self):
        calls = []
        def validator(e):
            calls.append(e)
        e = Element.with_attrs(validators=[validator])()
        self.assertFalse(e.is_valid())
        self.assertEqual(calls, [e])

    def test_validator_can_set_errors(self):
        def validator(e):
            e.validation_errors.append(u'Some error')
            return False
        e = Element.with_attrs(validators=[validator])()
        self.assertFalse(e.is_valid())
        self.assertEqual(e.validation_errors, [u'Some error'])

    def test_validator_exceptions_are_recorded_as_errors(self):
        error = TypeError()
        def validator(e):
            raise error
        e = Element.with_attrs(validators=[validator])()
        self.assertFalse(e.is_valid())
        self.assertEqual(e.validation_errors, [error])

    def test_can_be_valid(self):
        e = Element.with_attrs(validators=[lambda e: True])()
        self.assertTrue(e.is_valid())

    def test_multiple_validators_are_called_in_order(self):
        call_order = []
        def validator(order, value):
            def validator(e):
                call_order.append(order)
                return value
            return validator
        validators = [validator(i, i != 1) for i in xrange(3)]
        e = Element.with_attrs(validators=validators)()
        self.assertFalse(e.is_valid())
        self.assertEqual(call_order, range(2))

    def test_validation_is_recursive(self):
        calls = []
        def validator(e):
            calls.append(e)
            return True
        class MyElement(Element):
            validators = [validator]
            class a(Element):
                validators = [validator]
                class b(Element):
                    validators = [validator]
            class b(Element):
                validators = [validator]
        e = MyElement()
        self.assertTrue(e.is_valid())
        self.assertEqual(calls, [e['a']['b'], e['a'], e['b'], e])

    def test_invalid_child_doesnt_stop_recursion(self):
        calls = []
        def validator(value):
            def validator(e):
                calls.append(e)
                return value
            return validator
        class MyElement(Element):
            validators = [validator(True)]
            class a(Element):
                validators = [validator(False)]
                class b(Element):
                    validators = [validator(True)]
            class b(Element):
                validators = [validator(True)]
        e = MyElement()
        self.assertFalse(e.is_valid())
        self.assertEqual(calls, [e['a']['b'], e['a'], e['b'], e])


class TestListOf(unittest.TestCase):
    def test_extract_sub_items(self):
        @List.of
        class MyElement(Element):
            name = 'list'
        flat = dict(('list-%d' % (i,), i) for i in xrange(3))
        flat['list'] = 3
        flats = list(MyElement()._extract_sub_items(flat))
        flats.sort()
        self.assertEqual(flats, [(i, 'list', i) for i in xrange(3)])

    def test_extract_flats(self):
        @List.of
        class MyElement(Element):
            name = 'list'
        flats = list(MyElement()._extract_flats(
            dict(('list-%d' % (i,), i) for i in xrange(3))))
        self.assertEqual(flats, [{'list': i} for i in xrange(3)])

    def test_extract_flats_with_structure(self):
        @List.of
        class MyElement(Element):
            name = 'list'
            a = Element
            b = Element
        flat = {
            'list-0.a': 0,
            'list-0.b': 1,
            'list-1.a': 2,
            'list-1.b': 3,
        }
        flats = list(MyElement()._extract_flats(flat))
        self.assertEqual(flats, [{'list.a': i, 'list.b': i + 1}
                                 for i in xrange(0, 4, 2)])

    def test_from_flat(self):
        class MyElement(Element):
            name = 'list'
        MyList = List.of(MyElement)
        flat = dict(('list-%d' % (i,), i) for i in xrange(3))
        flat['list'] = '1'
        l = MyList.from_flat(flat)
        self.assertTrue(all(isinstance(el, MyElement) for el in l))
        self.assertEqual([el.value for el in l], range(3))
        self.assertEqual(l.value, '1')

    def test_from_flat_with_converter(self):
        class MyElement(Element):
            name = 'list'
            converter = int
        MyList = List.of(MyElement)
        flat = dict(('list-%d' % (i,), i) for i in xrange(3))
        flat['list'] = '1'
        l = MyList.from_flat(flat)
        self.assertTrue(all(isinstance(el, MyElement) for el in l))
        self.assertEqual([el.value for el in l], range(3))
        self.assertEqual(l.value, '1')

    def test_from_flat_with_structure(self):
        class MyElement(Element):
            @List.of
            class l(Element):
                a = Element
                class b(Element):
                    a = Element
            b = Element
        el = MyElement.from_flat({
            'l': 1,
            'l-2.a': 2,
            'l-2.b': 3,
            'l-2.b.a': 4,
            'l-12.a': 5,
            'l-12.b': 6,
            'l-12.b.a': 7,
            'b': 8,
        })
        self.assertEqual(el['l'].value, 1)
        self.assertEqual(el['l'][0]['a'].value, 2)
        self.assertEqual(el['l'][0]['b'].value, 3)
        self.assertEqual(el['l'][0]['b']['a'].value, 4)
        self.assertEqual(el['l'][1]['a'].value, 5)
        self.assertEqual(el['l'][1]['b'].value, 6)
        self.assertEqual(el['l'][1]['b']['a'].value, 7)
        self.assertEqual(el['b'].value, 8)

    def test_flatten(self):
        class MyElement(Element):
            @List.of
            class l(Element):
                a = Element
                class b(Element):
                    a = Element
            b = Element
        flat = {
            'l': 1,
            'l-0.a': 2,
            'l-0.b': 3,
            'l-0.b.a': 4,
            'l-1.a': 5,
            'l-1.b': 6,
            'l-1.b.a': 7,
            'b': 8,
        }
        el = MyElement.from_flat(flat)
        self.assertEqual(el.flatten(), flat)

    def test_validation(self):
        calls = []
        def validator(e):
            calls.append(e)
            return True
        class MyElement(Element):
            validators = [validator]
            @List.of
            class a(Element):
                validators = [validator]
            a = a.with_attrs(validators=[validator])
        e = MyElement()
        e['a'].extend(e['a'].element_type() for _ in xrange(3))
        self.assertTrue(e.is_valid())
        self.assertEqual(calls, [e['a'][0], e['a'][1], e['a'][2], e['a'], e])


class TestWithAttrs(unittest.TestCase):
    def test_calls_with_attrs_on_argument(self):
        class MyElement(Element):
            pass
        NewElement = with_attrs(MyElement, name='new name')
        self.assertEqual(NewElement.name, 'new name')

    def test_can_be_used_as_decorator(self):
        @with_attrs(name='new name')
        class MyElement(Element):
            pass
        self.assertEqual(MyElement.name, 'new name')

    def test_too_many_args_raises_typeerror(self):
        with self.assertRaises(TypeError) as assertion:
            with_attrs(1, 2)
        self.assertEqual(
            str(assertion.exception),
            'with_attrs() takes exactly 1 argument (2 given)'
        )


if __name__ == '__main__':
    unittest.main()
