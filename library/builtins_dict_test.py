#!/usr/bin/env python3
import unittest
from unittest.mock import Mock, call


class DictTests(unittest.TestCase):
    def test_repr_returns_string(self):
        self.assertEqual(dict.__repr__({}), "{}")
        self.assertEqual(dict.__repr__({42: 42}), "{42: 42}")
        self.assertEqual(
            dict.__repr__({1: 1, 2: 2, "hello": "hello"}),
            "{1: 1, 2: 2, 'hello': 'hello'}",
        )

        class M(type):
            def __repr__(cls):
                return "<M instance>"

        class C(metaclass=M):
            def __repr__(self):
                return "<C instance>"

        self.assertEqual(
            dict.__repr__({1: C, 2: C()}), "{1: <M instance>, 2: <C instance>}"
        )

    def test_repr_with_recursive_dict_prints_ellipsis(self):
        d = {}
        d[1] = d
        self.assertEqual(dict.__repr__(d), "{1: {...}}")

    def test_setitem_for_new_keys_keeps_insertion_order(self):
        d = {}
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        self.assertEqual(list(d.keys()), ["a", "b", "c"])

    def test_setitem_for_existing_key_preserves_order(self):
        d = {}
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        d["a"] = 100
        self.assertEqual(list(d.keys()), ["a", "b", "c"])
        self.assertIs(d["a"], 100)

    def test_setitem_for_deleted_key_inserted_last(self):
        d = {}
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        del d["a"]
        d["a"] = 100
        self.assertEqual(list(d.keys()), ["b", "c", "a"])
        self.assertIs(d["a"], 100)

    def test_clear_with_non_dict_raises_type_error(self):
        with self.assertRaises(TypeError):
            dict.clear(None)

    def test_clear_removes_all_elements(self):
        d = {"a": 1}
        self.assertEqual(dict.clear(d), None)
        self.assertEqual(d.__len__(), 0)
        self.assertNotIn("a", d)

    def test_copy_with_non_dict_self_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            dict.copy(None)
        self.assertIn(
            "'copy' requires a 'dict' object but received a 'NoneType'",
            str(context.exception),
        )

    def test_dunder_hash_is_none(self):
        self.assertIs(dict.__hash__, None)

    def test_fromkeys_with_non_iterable_raises_type_error(self):
        with self.assertRaisesRegex(TypeError, "'int' object is not iterable"):
            dict.fromkeys(5, ())

    def test_fromkeys_calls_dunder_iter_on_iterable(self):
        class C:
            def __iter__(self):
                return [1, 2, 3].__iter__()

        result = dict.fromkeys(C())
        self.assertDictEqual(result, {1: None, 2: None, 3: None})

    def test_fromkeys_sets_dict_values_to_given_value(self):
        class C:
            def __iter__(self):
                return [1, 2, 3].__iter__()

        result = dict.fromkeys(C(), "abc")
        self.assertDictEqual(result, {1: "abc", 2: "abc", 3: "abc"})

    def test_fromkeys_calls_subclass_dunder_init(self):
        class C(dict):
            __init__ = Mock(name="__init__", return_value=None)

        result = C.fromkeys(())
        self.assertDictEqual(result, {})
        C.__init__.assert_called_once()

    def test_fromkeys_calls_subclass_dunder_new(self):
        class C(dict):
            __new__ = Mock(name="__new__", return_value={})

        result = C.fromkeys(())
        self.assertDictEqual(result, {})
        C.__new__.assert_called_once()

    def test_fromkeys_calls_subclass_dunder_setitem(self):
        class C(dict):
            __setitem__ = Mock(name="__setitem__", return_value={})

        result = C.fromkeys((1, 2, 3))
        self.assertDictEqual(result, {})
        C.__setitem__.assert_has_calls([call(1, None), call(2, None), call(3, None)])

    def test_update_with_malformed_sequence_elt_raises_type_error(self):
        with self.assertRaises(ValueError):
            dict.update({}, [("a",)])

    def test_update_with_no_params_does_nothing(self):
        d = {"a": 1}
        d.update()
        self.assertEqual(len(d), 1)

    def test_update_with_mapping_adds_elements(self):
        d = {"a": 1}
        d.update([("a", "b"), ("c", "d")])
        self.assertIn("a", d)
        self.assertIn("c", d)
        self.assertEqual(d["a"], "b")
        self.assertEqual(d["c"], "d")

    def test_update_with_mapping_of_non_pair_tuple_raises_value_error(self):
        mapping = [("a", "b"), ("c", "d", "e")]
        d = {}
        with self.assertRaises(ValueError) as context:
            d.update(mapping)
        self.assertIn(
            "dictionary update sequence element #1 has length 3; 2 is required",
            str(context.exception),
        )

    def test_update_with_keys_attribute_calls_keys_method(self):
        class C:
            keys = Mock(name="keys", return_value=())
            __getitem__ = Mock(name="__getitem__")

        c = C()
        {}.update(c)
        c.keys.assert_called_once()

    def test_update_with_raising_keys_method_propagates_exception(self):
        class C:
            keys = Mock(name="keys", side_effect=Exception("foo"))
            __getitem__ = Mock(name="__getitem__")

        c = C()
        with self.assertRaisesRegex(Exception, "foo"):
            {}.update(c)
        c.keys.assert_called_once()
        c.__getitem__.assert_not_called()

    def test_update_with_keys_instance_attribute_calls_keys(self):
        class C:
            pass

        d = {}
        c = C()
        c.keys = Mock(name="keys", return_value=())
        c.__getitem__ = Mock(name="__getitem__")
        d.update(c)
        c.keys.assert_called_once()

    def test_update_with_keys_calls_dunder_iter_on_result(self):
        class D:
            __iter__ = Mock(name="__iter__", return_value=[].__iter__())

        iterable = D()

        class C:
            keys = Mock(name="keys", return_value=iterable)
            __getitem__ = Mock(name="__getitem__")

        c = C()
        {}.update(c)
        iterable.__iter__.assert_called_once()

    def test_update_with_keys_attribute_calls_getitem_with_key(self):
        class C:
            def keys(self):
                return ("foo", "bar")

            __getitem__ = Mock(name="__getitem__", return_value="baz")

        d = {}
        c = C()
        d.update(c)
        self.assertEqual(c.__getitem__.call_count, 2)
        self.assertEqual(d["foo"], "baz")
        self.assertEqual(d["bar"], "baz")

    def test_update_with_kwargs_returns_updated_dict(self):
        d1 = {"a": 1, "b": 2}
        d1.update(y=25)
        self.assertEqual(d1["y"], 25)

    def test_update_with_dict_and_kwargs_returns_updated_dict(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"a": 10, "b": 11}
        d1.update(d2, b=20)
        self.assertEqual(d1["a"], 10)
        self.assertEqual(d1["b"], 20)

    def test_update_with_self_and_other_kwargs_adds_to_dict(self):
        d1 = {}
        d1.update(self="hello", seq="world")
        self.assertEqual(d1["self"], "hello")
        self.assertEqual(d1["seq"], "world")

    def test_dunder_delitem_with_none_dunder_hash(self):
        class C:
            __hash__ = None

        with self.assertRaises(TypeError):
            dict.__delitem__({}, C())

    def test_dunder_delitem_propagates_exceptions_from_dunder_hash(self):
        class C:
            def __hash__(self):
                raise UserWarning("foo")

        with self.assertRaises(UserWarning):
            dict.__delitem__({}, C())

    def test_concrete_dict_has_no_dunder_missing(self):
        with self.assertRaises(AttributeError):
            dict.__missing__

    def test_dunder_getitem_calls_dunder_missing(self):
        class C(dict):
            def __missing__(self, key):
                raise UserWarning("foo")

        result = C()
        self.assertRaises(UserWarning, result.__getitem__, "hello")

    def test_dunder_eq_with_different_item_count_returns_false(self):
        d0 = {4: 0}
        d1 = {4: 0, 8: 0}
        self.assertFalse(dict.__eq__(d0, d1))
        self.assertFalse(dict.__eq__(d1, d0))
        self.assertFalse(dict.__eq__({}, d0))
        self.assertFalse(dict.__eq__(d1, {}))

    def test_dunder_eq_with_different_keys_returns_false(self):
        d0 = {4: 0, "b": 17}
        d1 = {4: 0, "c": 17}
        self.assertFalse(dict.__eq__(d0, d1))

    def test_dunder_eq_with_different_values_returns_false(self):
        d0 = {4: 0, "b": 17}
        d1 = {4: 0, "b": 15}
        self.assertFalse(dict.__eq__(d0, d1))

    def test_dunder_eq_returns_true(self):
        self.assertTrue(dict.__eq__({}, {}))
        nan = float("nan")
        d0 = {4: "b", "a": 88, 42: nan, None: (42.42, b"x")}
        d1 = {4: "b", "a": 88, 42: nan, None: (42.42, b"x")}
        self.assertFalse(d0 is d1)
        self.assertTrue(dict.__eq__(d0, d1))

    def test_dunder_eq_checks_identity_before_calling_dunder_eq(self):
        class C:
            def __eq__(self, other):
                return False

        i = C()
        d0 = {"a": i}
        d1 = {"a": i}
        self.assertTrue(dict.__eq__(d0, d1))

    def test_dunder_eq_with_non_dict_returns_not_implemented(self):
        self.assertIs(dict.__eq__({}, "not a dict"), NotImplemented)

    def test_dunder_eq_calls_dunder_bool(self):
        class B:
            def __bool__(self):
                raise UserWarning()

        class C:
            def __eq__(self, other):
                return B()

            def __hash__(self):
                return 0

        d0 = {0: C()}
        d1 = {0: C()}
        with self.assertRaises(UserWarning):
            dict.__eq__(d0, d1)

    def test_dunder_ne_returns_not_eq(self):
        nan = float("nan")
        d0 = {4: "b", "a": 88, 42: nan, None: (42.42, b"x")}
        d1 = {4: "b", "a": 88, 42: nan, None: (42.42, b"x")}
        self.assertFalse(d0.__ne__(d1))
        self.assertTrue(d0.__ne__({}))

    def test_dunder_ne_returns_not_implemented_if_wrong_types(self):
        orig = {4: "b", "a": 88, None: (42.42, b"x")}
        self.assertIs(orig.__ne__(1), NotImplemented)
        self.assertIs(orig.__ne__([]), NotImplemented)

    def test_mix_bool_and_int_keys(self):
        d = {}
        d[True] = 42
        self.assertIn(1, d)
        self.assertEqual(d[True], 42)
        self.assertEqual(d[1], 42)
        self.assertNotIn(False, d)
        d[1] = "foo"
        self.assertEqual(len(d), 1)
        self.assertEqual(d[True], "foo")
        self.assertEqual(d[1], "foo")
        self.assertNotIn(False, d)

        d[0] = "bar"
        self.assertEqual(d[False], "bar")
        self.assertEqual(d[0], "bar")
        d[False] = "bar"
        self.assertEqual(len(d), 2)

    def test_popitem_with_non_dict_raise_type_error(self):
        with self.assertRaises(TypeError) as context:
            dict.popitem(None)
        self.assertIn("'popitem' requires a 'dict' object", str(context.exception))

    def test_popitem_with_empty_dict_raises_key_error(self):
        d = {}
        with self.assertRaises(KeyError) as context:
            dict.popitem(d)
        self.assertIn("popitem(): dictionary is empty", str(context.exception))

    def test_popitem_deletes_last_inserted_item_and_returns_it(self):
        d = {"a": 1, "b": 2, "c": 3}
        self.assertEqual(len(d), 3)
        key0, value0 = dict.popitem(d)
        key1, value1 = dict.popitem(d)
        key2, value2 = dict.popitem(d)
        self.assertEqual((key0, value0), ("c", 3))
        self.assertEqual((key1, value1), ("b", 2))
        self.assertEqual((key2, value2), ("a", 1))
        self.assertEqual(len(d), 0)

    def test_update_with_tuple_keys_propagates_exceptions_from_dunder_hash(self):
        class C:
            def __hash__(self):
                raise UserWarning("foo")

        class D:
            def keys(self):
                return (C(),)

            def __getitem__(self, key):
                return "foo"

        with self.assertRaises(UserWarning):
            dict.update({}, D())

    def test_update_with_list_keys_propagates_exceptions_from_dunder_hash(self):
        class C:
            def __hash__(self):
                raise UserWarning("foo")

        class D:
            def keys(self):
                return [C()]

            def __getitem__(self, key):
                return "foo"

        with self.assertRaises(UserWarning):
            dict.update({}, D())

    def test_update_with_iter_keys_propagates_exceptions_from_dunder_hash(self):
        class C:
            def __hash__(self):
                raise UserWarning("foo")

        class D:
            def keys(self):
                return [C()].__iter__()

            def __getitem__(self, key):
                return "foo"

        with self.assertRaises(UserWarning):
            dict.update({}, D())


class DictItemsTests(unittest.TestCase):
    DictItemsType = type({}.items())

    def test_dunder_and_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__and__({}.keys(), [])
        self.assertIn(
            "'__and__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_and_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.items().__and__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_and_with_iterable_returns_set_with_intersection(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.items().__and__([("hello", "world"), ("fizz", "buzz")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})

    def test_dunder_and_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.items().__and__()

    def test_dunder_and_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.items().__and__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_and_with_empty_lhs_and_non_empty_rhs_returns_empty_set(self):
        result = {}.items().__and__([("hello", "world")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_and_with_non_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {"hello": "world"}.items().__and__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_eq_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__eq__({}.keys(), [])
        self.assertIn(
            "'__eq__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_eq_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.items().__eq__()

    def test_dunder_eq_with_empty_lhs_and_empty_rhs_returns_true(self):
        self.assertIs({}.items().__eq__(set()), True)

    def test_dunder_eq_with_empty_lhs_and_non_empty_rhs_returns_false(self):
        self.assertIs({}.items().__eq__(set("foo")), False)

    def test_dunder_eq_with_non_empty_lhs_and_empty_rhs_returns_false(self):
        self.assertIs({"hello": "world"}.items().__eq__(set()), False)

    def test_dunder_eq_with_non_set_or_dictview_rhs_returns_notimplemented(self):
        self.assertIs({"hello": "world"}.items().__eq__(()), NotImplemented)

    def test_dunder_eq_with_set_rhs(self):
        self.assertIs({"hello": "world"}.items().__eq__({("hello", "world")}), True)

    def test_dunder_eq_with_frozenset_rhs(self):
        self.assertIs(
            {"hello": "world"}.items().__eq__(frozenset({("hello", "world")})), True
        )

    def test_dunder_eq_with_dict_items_rhs(self):
        mapping = {"hello": "world"}
        self.assertIs(mapping.items().__eq__(mapping.items()), True)

    def test_dunder_eq_with_dict_keys_rhs(self):
        mapping = {"hello": "world"}
        other_mapping = {("hello", "world"): "baz"}
        self.assertIs(mapping.items().__eq__(other_mapping.keys()), True)

    def test_dunder_eq_with_dict_values_rhs_returns_notimplemented(self):
        mapping = {"hello": "world"}
        self.assertIs(mapping.items().__eq__(mapping.values()), NotImplemented)

    def test_dunder_eq_with_different_lengths_returns_false(self):
        mapping = {"hello": "world"}
        other_mapping = {"hello": "world", "foo": "bar"}
        self.assertIs(mapping.items().__eq__(other_mapping.items()), False)

    def test_dunder_eq_with_id_equal_but_inequal_element_returns_true(self):
        class C:
            def __eq__(self, other):
                return False

            def __hash__(self):
                return 1

        instance = C()
        self.assertIs({instance: "world"}.items().__eq__({(instance, "world")}), True)

    def test_dunder_repr_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__repr__({}.keys())
        self.assertIn(
            "'__repr__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_repr_prints_items(self):
        result = repr({"hello": "world", "foo": "bar"}.items())
        self.assertEqual(result, "dict_items([('hello', 'world'), ('foo', 'bar')])")

    def test_dunder_repr_with_recursive_prints_ellipsis(self):
        x = {}
        x[1] = x.items()
        self.assertEqual(repr(x.items()), "dict_items([(1, dict_items([(1, ...)]))])")

    def test_dunder_repr_calls_key_dunder_repr(self):
        class C:
            def __repr__(self):
                return "foo"

        result = repr({"hello": C()}.items())
        self.assertEqual(result, "dict_items([('hello', foo)])")

    def test_recursive_dunder_repr(self):
        circular_mapping = {}
        circular_mapping["hello"] = circular_mapping.items()
        self.assertEqual(
            repr(circular_mapping.items()),
            "dict_items([('hello', dict_items([('hello', ...)]))])",
        )

    def test_dunder_len_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__len__({}.keys())
        self.assertIn(
            "'__len__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_len_with_non_dict_items_raises_type_error(self):
        dict_items = type({}.items())
        with self.assertRaisesRegex(
            TypeError, "requires a 'dict_items' object but .+ 'int'"
        ):
            dict_items.__len__(5)

    def test_dunder_len_returns_length_of_underlying_dict(self):
        mapping = {"hello": "world", "foo": "bar"}
        items = mapping.items()
        self.assertEqual(items.__len__(), 2)
        mapping["szechuan"] = "broccoli"
        self.assertEqual(items.__len__(), 3)

    def test_dunder_or_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__or__({}.keys(), [])
        self.assertIn(
            "'__or__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_or_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.items().__or__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_or_with_iterable_returns_set_with_union(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.items().__or__([("hello", "baz")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world"), ("foo", "bar"), ("hello", "baz")})

    def test_dunder_or_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.items().__or__()

    def test_dunder_or_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.items().__or__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_or_with_empty_lhs_and_non_empty_rhs_returns_rhs(self):
        result = {}.items().__or__([("hello", "world")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})

    def test_dunder_or_with_non_empty_lhs_and_empty_rhs_adds_none(self):
        result = {"hello": "world"}.items().__or__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})

    def test_dunder_ror_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__ror__({}.keys(), [])
        self.assertIn(
            "'__ror__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_ror_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.items().__ror__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_ror_with_iterable_returns_set_with_union(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.items().__ror__([("hello", "baz")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world"), ("foo", "bar"), ("hello", "baz")})

    def test_dunder_ror_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.items().__ror__()

    def test_dunder_ror_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.items().__ror__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_ror_with_empty_lhs_and_non_empty_rhs_returns_rhs(self):
        result = {}.items().__ror__([("hello", "world")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})

    def test_dunder_ror_with_non_empty_lhs_and_empty_rhs_adds_none(self):
        result = {"hello": "world"}.items().__ror__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})

    def test_dunder_sub_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__sub__({}.keys(), [])
        self.assertIn(
            "'__sub__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_sub_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.items().__sub__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_sub_with_nonexistent_pair_does_not_remove_pair(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.items().__sub__([("hello", "baz")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world"), ("foo", "bar")})

    def test_dunder_sub_with_list_containing_pair_removes_pair(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.items().__sub__([("hello", "world")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("foo", "bar")})

    def test_dunder_sub_with_list_removes_all_pairs_in_list(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.items().__sub__([("hello", "world"), ("foo", "bar")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_sub_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.items().__sub__()

    def test_dunder_sub_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.items().__sub__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_sub_with_empty_lhs_and_non_empty_rhs_returns_empty_set(self):
        result = {}.items().__sub__([("hello", "world")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_sub_with_non_empty_lhs_and_empty_rhs_removes_none(self):
        result = {"hello": "world"}.items().__sub__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})

    def test_dunder_xor_with_non_dict_items_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictItemsType.__xor__({}.keys(), [])
        self.assertIn(
            "'__xor__' requires a 'dict_items' object but received a 'dict_keys'",
            str(context.exception),
        )

    def test_dunder_xor_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.items().__xor__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_xor_with_iterable_returns_set_with_xor(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.items().__xor__([("hello", "world"), ("fizz", "buzz")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("foo", "bar"), ("fizz", "buzz")})

    def test_dunder_xor_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.items().__xor__()

    def test_dunder_xor_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.items().__xor__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_xor_with_empty_lhs_and_non_empty_rhs_returns_rhs(self):
        result = {}.items().__xor__([("hello", "world")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})

    def test_dunder_xor_with_non_empty_lhs_and_empty_rhs_removes_none(self):
        result = {"hello": "world"}.items().__xor__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {("hello", "world")})


class DictKeysTests(unittest.TestCase):
    DictKeysType = type({}.keys())

    def test_dunder_and_with_non_dict_keys_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictKeysType.__and__({}.items(), [])
        self.assertIn(
            "'__and__' requires a 'dict_keys' object but received a 'dict_items'",
            str(context.exception),
        )

    def test_dunder_and_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.keys().__and__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_and_with_iterable_returns_set_with_intersection(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.keys().__and__(["hello", "fizz"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})

    def test_dunder_and_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.keys().__and__()

    def test_dunder_and_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.keys().__and__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_and_with_empty_lhs_and_non_empty_rhs_returns_empty_set(self):
        result = {}.keys().__and__(["hello"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_and_with_non_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {"hello": "world"}.keys().__and__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_eq_with_non_dict_keys_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictKeysType.__eq__({}.items(), [])
        self.assertIn(
            "'__eq__' requires a 'dict_keys' object but received a 'dict_items'",
            str(context.exception),
        )

    def test_dunder_eq_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.keys().__eq__()

    def test_dunder_eq_with_empty_lhs_and_empty_rhs_returns_true(self):
        self.assertIs({}.keys().__eq__(set()), True)

    def test_dunder_eq_with_empty_lhs_and_non_empty_rhs_returns_false(self):
        self.assertIs({}.keys().__eq__(set("foo")), False)

    def test_dunder_eq_with_non_empty_lhs_and_empty_rhs_returns_false(self):
        self.assertIs({"hello": "world"}.keys().__eq__(set()), False)

    def test_dunder_eq_with_non_set_or_dictview_rhs_returns_notimplemented(self):
        self.assertIs({"hello": "world"}.keys().__eq__(()), NotImplemented)

    def test_dunder_eq_with_set_rhs(self):
        self.assertIs({"hello": "world"}.keys().__eq__({"hello"}), True)

    def test_dunder_eq_with_frozenset_rhs(self):
        self.assertIs({"hello": "world"}.keys().__eq__(frozenset({"hello"})), True)

    def test_dunder_eq_with_dict_items_rhs(self):
        self.assertIs({"hello": "world"}.keys().__eq__({"hello": "world"}.keys()), True)

    def test_dunder_eq_with_dict_keys_rhs(self):
        mapping = {("hello", "world"): "baz"}
        other_mapping = {"hello": "world"}
        self.assertIs(mapping.keys().__eq__(other_mapping.items()), True)

    def test_dunder_eq_with_dict_values_rhs_returns_notimplemented(self):
        mapping = {"hello": "world"}
        self.assertIs(mapping.keys().__eq__(mapping.values()), NotImplemented)

    def test_dunder_eq_with_different_lengths_returns_false(self):
        mapping = {"hello": "world"}
        other_mapping = {"hello": "world", "foo": "bar"}
        self.assertIs(mapping.keys().__eq__(other_mapping.keys()), False)

    def test_dunder_eq_with_id_equal_but_inequal_element_returns_true(self):
        class C:
            def __eq__(self, other):
                return False

            def __hash__(self):
                return 1

        instance = C()
        self.assertIs({instance: "world"}.keys().__eq__({instance}), True)

    def test_dunder_repr_with_non_dict_keys_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictKeysType.__repr__({}.items())
        self.assertIn(
            "'__repr__' requires a 'dict_keys' object but received a 'dict_items'",
            str(context.exception),
        )

    def test_dunder_repr_prints_keys(self):
        result = repr({"hello": "world", "foo": "bar"}.keys())
        self.assertEqual(result, "dict_keys(['hello', 'foo'])")

    def test_dunder_repr_with_recursive_prints_ellipsis(self):
        x = {}
        x[1] = x.values()
        self.assertEqual(repr(x.values()), "dict_values([dict_values([...])])")

    def test_dunder_repr_calls_key_dunder_repr(self):
        class C:
            def __repr__(self):
                return "foo"

        result = repr({C(): "world"}.keys())
        self.assertEqual(result, "dict_keys([foo])")

    def test_recursive_dunder_repr(self):
        class C:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return self is other

            def __hash__(self):
                return 5

            def __repr__(self):
                return self.value.__repr__()

        circular_mapping = {}
        circular_mapping[C(circular_mapping.keys())] = 10
        self.assertEqual(repr(circular_mapping.keys()), "dict_keys([dict_keys([...])])")

    def test_dunder_len_with_non_dict_keys_raises_type_error(self):
        with self.assertRaisesRegex(
            TypeError, "requires a 'dict_keys' object but .+ 'int'"
        ):
            self.DictKeysType.__len__(5)

    def test_dunder_len_returns_length_of_underlying_dict(self):
        mapping = {"hello": "world", "foo": "bar"}
        keys = mapping.keys()
        self.assertEqual(keys.__len__(), 2)
        mapping["szechuan"] = "broccoli"
        self.assertEqual(keys.__len__(), 3)

    def test_dunder_or_with_non_dict_keys_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictKeysType.__or__({}.items(), [])
        self.assertIn(
            "'__or__' requires a 'dict_keys' object but received a 'dict_items'",
            str(context.exception),
        )

    def test_dunder_or_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.keys().__or__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_or_with_iterable_returns_set_with_union(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.keys().__or__(["baz"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello", "foo", "baz"})

    def test_dunder_or_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.keys().__or__()

    def test_dunder_or_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.keys().__or__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_or_with_empty_lhs_and_non_empty_rhs_returns_rhs(self):
        result = {}.keys().__or__(["hello"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})

    def test_dunder_or_with_non_empty_lhs_and_empty_rhs_adds_none(self):
        result = {"hello": "world"}.keys().__or__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})

    def test_dunder_ror_with_non_dict_keys_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictKeysType.__ror__({}.items(), [])
        self.assertIn(
            "'__ror__' requires a 'dict_keys' object but received a 'dict_items'",
            str(context.exception),
        )

    def test_dunder_ror_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.keys().__ror__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_ror_with_iterable_returns_set_with_union(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.keys().__ror__(["baz"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello", "foo", "baz"})

    def test_dunder_ror_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.keys().__ror__()

    def test_dunder_ror_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.keys().__ror__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_ror_with_empty_lhs_and_non_empty_rhs_returns_rhs(self):
        result = {}.keys().__ror__(["hello"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})

    def test_dunder_ror_with_non_empty_lhs_and_empty_rhs_adds_none(self):
        result = {"hello": "world"}.keys().__ror__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})

    def test_dunder_sub_with_non_dict_keys_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictKeysType.__sub__({}.items(), [])
        self.assertIn(
            "'__sub__' requires a 'dict_keys' object but received a 'dict_items'",
            str(context.exception),
        )

    def test_dunder_sub_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.keys().__sub__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_sub_with_nonexistent_key_does_not_remove_pair(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.keys().__sub__(["baz"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello", "foo"})

    def test_dunder_sub_with_list_containing_key_removes_key(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.keys().__sub__(["hello"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"foo"})

    def test_dunder_sub_with_list_removes_all_keys_in_list(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.keys().__sub__(["hello", "foo"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_sub_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.keys().__sub__()

    def test_dunder_sub_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.keys().__sub__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_sub_with_empty_lhs_and_non_empty_rhs_returns_empty_set(self):
        result = {}.keys().__sub__([("hello", "world")])
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_sub_with_non_empty_lhs_and_empty_rhs_removes_none(self):
        result = {"hello": "world"}.keys().__sub__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})

    def test_dunder_xor_with_non_dict_keys_lhs_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.DictKeysType.__xor__({}.items(), [])
        self.assertIn(
            "'__xor__' requires a 'dict_keys' object but received a 'dict_items'",
            str(context.exception),
        )

    def test_dunder_xor_with_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError) as context:
            {"hello": "world", "foo": "bar"}.keys().__xor__(5)
        self.assertEqual("'int' object is not iterable", str(context.exception))

    def test_dunder_xor_with_iterable_returns_set_with_xor(self):
        mapping = {"hello": "world", "foo": "bar"}
        result = mapping.keys().__xor__(["hello", "fizz"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"foo", "fizz"})

    def test_dunder_xor_with_no_rhs_raises_type_error(self):
        with self.assertRaises(TypeError):
            {"hello": "world"}.keys().__xor__()

    def test_dunder_xor_with_empty_lhs_and_empty_rhs_returns_empty_set(self):
        result = {}.keys().__xor__(())
        self.assertIsInstance(result, set)
        self.assertEqual(result, set())

    def test_dunder_xor_with_empty_lhs_and_non_empty_rhs_returns_rhs(self):
        result = {}.keys().__xor__(["hello"])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})

    def test_dunder_xor_with_non_empty_lhs_and_empty_rhs_removes_none(self):
        result = {"hello": "world"}.keys().__xor__([])
        self.assertIsInstance(result, set)
        self.assertEqual(result, {"hello"})


class DictValuesTests(unittest.TestCase):
    def test_dunder_repr_prints_values(self):
        result = repr({"hello": "world", "foo": "bar"}.values())
        self.assertEqual(result, "dict_values(['world', 'bar'])")

    def test_dunder_repr_calls_key_dunder_repr(self):
        class C:
            def __repr__(self):
                return "foo"

        result = repr({"hello": C()}.values())
        self.assertEqual(result, "dict_values([foo])")

    def test_recursive_dunder_repr(self):
        circular_mapping = {}
        circular_mapping["hello"] = circular_mapping.values()
        self.assertEqual(
            repr(circular_mapping.values()), "dict_values([dict_values([...])])"
        )

    def test_dunder_len_with_non_dict_values_raises_type_error(self):
        dict_values = type({}.values())
        with self.assertRaisesRegex(
            TypeError, "requires a 'dict_values' object but .+ 'int'"
        ):
            dict_values.__len__(5)

    def test_dunder_len_returns_length_of_underlying_dict(self):
        mapping = {"hello": "world", "foo": "bar"}
        values = mapping.values()
        self.assertEqual(values.__len__(), 2)
        mapping["szechuan"] = "broccoli"
        self.assertEqual(values.__len__(), 3)


if __name__ == "__main__":
    unittest.main()