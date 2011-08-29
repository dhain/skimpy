import unittest

from skimpy.element import *


class TestElement(unittest.TestCase):
    def test_get_returns_copy_bound_to_parent(self):
        class A(object):
            element = Element
        self.assertIsNot(A.element, Element)
        self.assertIs(A.element.parent, A)

    def test_get_on_instance_returns_instance_bound_to_parent_instance(self):
        class A(Element):
            element = Element
        a = A()
        self.assertTrue(isinstance(a.element, Element))
        self.assertIs(a.element.parent, a)

    def test_subsequent_instance_gets_return_same_instance(self):
        class A(Element):
            element = Element
        a = A()
        self.assertIs(a.element, a.element)

    def test_get_works_with_element_subclass(self):
        class MyElement(Element):
            pass
        class A(object):
            element = MyElement
        self.assertIsNot(A.element, MyElement)
        self.assertIs(A.element.parent, A)

    def test_get_works_with_parent_subclass(self):
        class MyElement(Element):
            pass
        class A(object):
            element = MyElement
        class B(A):
            pass
        self.assertIsNot(B.element, MyElement)
        self.assertIs(B.element.parent, B)

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
        self.assertEqual(E1.E2.E3.path, 'E2.E3')

    def test_path_works_when_supplanted(self):
        class E1(Element):
            class E2(Element):
                class E3(Element):
                    pass
        class E4(Element):
            pass
        E4.E3 = E1.E2.E3
        self.assertEqual(E4.E3.path, 'E3')

    def test_path_with_custom_names(self):
        class E1(Element):
            e2 = type('E2', (Element,), {'e3': Element})
        self.assertEqual(E1.e2.e3.path, 'e2.e3')

    def test_can_have_no_children(self):
        self.assertEqual(Element.children, set())

    def test_keeps_track_of_children(self):
        class E(Element):
            a = Element
            b = Element
            c = Element
        self.assertEqual(E.children, set('a b c'.split()))

    def test_child_keeps_track_of_children(self):
        class E1(Element):
            class E2(Element):
                a = Element
                b = Element
                c = Element
        self.assertEqual(E1.E2.children, set('a b c'.split()))

    def test_inherits_children_from_superclass(self):
        class E1(Element):
            a = type('E1a', (Element,), {})
        class E2(Element):
            a = type('E2a', (Element,), {})
        class E3(E1, E2):
            b = Element
        self.assertEqual(E3.children, set('a b'.split()))
        self.assertEqual(E3.a.__name__, 'E1a')

    def test_subclass_can_have_init_args(self):
        class MyElement(Element):
            def __init__(self, arg1):
                pass
        self.assertTrue(isinstance(MyElement(1), MyElement))

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
        self.assertEqual(e.a.value, 1)
        self.assertEqual(e.b.value, 2)
        self.assertEqual(e.c.value, 3)
        self.assertEqual(e.c.a.value, 4)
        self.assertEqual(e.c.b.value, 5)
        self.assertEqual(e.c.c.value, None)


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
        l = MyList.from_flat(dict(('list-%d' % (i,), i) for i in xrange(3)))
        self.assertTrue(all(isinstance(el, MyElement) for el in l))
        self.assertEqual([el.value for el in l], range(3))

    def test_from_flat_with_structure(self):
        class MyElement(Element):
            @List.of
            class a(Element):
                a = Element
                class b(Element):
                    a = Element
            b = Element
        el = MyElement.from_flat({
            'a': 1,
            'a-2.a': 2,
            'a-2.b': 3,
            'a-2.b.a': 4,
            'a-12.a': 5,
            'a-12.b': 6,
            'a-12.b.a': 7,
            'b': 8,
        })
        self.assertEqual(el.a.value, 1)
        self.assertEqual(el.a[0].a.value, 2)
        self.assertEqual(el.a[0].b.value, 3)
        self.assertEqual(el.a[0].b.a.value, 4)
        self.assertEqual(el.a[1].a.value, 5)
        self.assertEqual(el.a[1].b.value, 6)
        self.assertEqual(el.a[1].b.a.value, 7)
        self.assertEqual(el.b.value, 8)


if __name__ == '__main__':
    unittest.main()
