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

    def test_default_name_is_class_name(self):
        class MyElement(Element):
            pass
        self.assertEqual(MyElement.name, 'MyElement')

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
        self.assertEqual(E1.E2.E3.path, 'E1.E2.E3')

    def test_path_works_when_supplanted(self):
        class E1(Element):
            class E2(Element):
                class E3(Element):
                    pass
        class E4(Element):
            pass
        E4.E3 = E1.E2.E3
        self.assertEqual(E4.E3.path, 'E4.E3')

    def test_path_stops_when_parent_has_no_name(self):
        class P1(object):
            class E2(Element):
                class E3(Element):
                    pass
        self.assertEqual(P1.E2.E3.path, 'E2.E3')

    def test_path_with_custom_names(self):
        class E1(Element):
            e2 = type('E2', (Element,), {'e3': Element})
        self.assertEqual(E1.e2.e3.path, 'E1.e2.e3')

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
            a = Element
        class E2(E1):
            b = Element
        self.assertEqual(E2.children, set('a b'.split()))


if __name__ == '__main__':
    unittest.main()
