"""
B+ Tree class and methods.
"""

import logging
import math
from copy import deepcopy
from functools import wraps

from exceptions import *
from node import Node

logger = logging.getLogger(__name__)

# CLRS degree (lower bound) d <= # of node <= 2d
# Knuth Order (upper bound) ceil(k/2) <= # of node <= k
# https://stackoverflow.com/questions/28846377/

# FILL_FACTOR = 0.5


class BPlusTree:
    """B+ Tree."""

    def __init__(self, order: int) -> None:
        """Initialize B+ tree as a root with given order."""
        self.order = order
        self.root = Node(self.order, leaf=True)

    def _display_bplus_tree(func):
        """A decorator for displaying B+ tree after performing an operation."""

        @wraps(func)
        def wrapper(self, data):
            func(self, data)
            self.display()

        return wrapper

    # ---------------------------------------------------------------------------- #
    #                                    modules                                   #
    # ---------------------------------------------------------------------------- #
    def _search_min_key_in_subtree(self, node: Node | int) -> int:
        """Search for the lowest and leftmost key in subtree.

        :param node: root of subtree or a data in leaf
        :type node: Node | int
        :return: minimum key
        :rtype: int
        """
        if isinstance(node, list):
            return node[0]

        while not node.leaf:
            node = node.values[0]
        return node.keys[0]

    def _search_position_in_child(self, node: Node, data: int) -> tuple[Node, int]:
        """Get the appropriate position in child nodes to insert given data.

        :param node: parent node
        :type node: Node
        :param data: data to insert
        :type data: int
        :return: child node to be inserted to, index of it in original child
        :rtype: tuple[Node, int]
        """
        for i, key in enumerate(node.keys):
            if data < key:
                return node.values[i], i  # left child of the key of greater value
        return node.values[i + 1], i + 1  # rightmost child

    def _merge_into_parent(self, node: Node, idx: int) -> None:
        """Merge a splitted node into its parent.

        After splitting a node into parent, left, and right, merge the key of parent
        into grandparent and the child of parent (left and right) into grandparent's
        child.

        :param node: splitted node
        :type node: Node
        :param idx: index of splitted node in its parent's child
        :type idx: int
        """
        logger.debug("Merge")

        # remove node from parent's child
        parent = node.parent
        parent.values.pop(idx)

        # update parents of current node's child before inserting them into parent
        for child in node.values:
            child.parent = parent

        # linear search and insertion
        pivot = node.keys[0]
        for i, key in enumerate(parent.keys):
            if pivot < key:
                parent.keys = parent.keys[:i] + [pivot] + parent.keys[i:]
                parent.values = parent.values[:i] + node.values + parent.values[i:]
                return

        parent.keys.append(pivot)
        parent.values.extend(node.values)

    def _rotate(self, node: Node) -> tuple[Node, int, int]:
        """Rotate a redundant child from current node to left or right sibling.

        :param node: node to rotate
        :type node: Node
        :raises RotateError: raise if there's no sibling or enough slots for rotation
        :return: node whose minimum key has changed, old minimum key, new minimum key
        :rtype: tuple[Node, int, int]
        """
        if node.prev is not None and len(node.prev.keys) < self.order:
            return self._left_rotate(node)
        if node.next is not None and len(node.next.keys) < self.order:
            return self._right_rotate(node)
        raise RotateError

    def _left_rotate(self, node: Node) -> tuple[Node, int, int]:
        """Move current node's leftmost key and child into left sibling.

        :param node: node to rotate
        :type node: Node
        :return: node whose minimum key has changed, old minimum key, new minimum key
        :rtype: tuple[Node, int, int]
        """
        logger.debug("Rotate to left")
        left_sibling = node.prev

        # old and new minimum key of current node
        old_min_key = self._search_min_key_in_subtree(node.values[0])
        new_min_key = self._search_min_key_in_subtree(node.values[1])

        # insert current subtree's minimum key and child into left sibling
        left_sibling.keys.append(old_min_key)
        left_sibling.values.append(node.values[0])

        node.keys.pop(0)
        node.values.pop(0)

        if not left_sibling.leaf:
            left_sibling.values[-1].parent = left_sibling
        return node.parent, old_min_key, new_min_key

    def _right_rotate(self, node: Node) -> tuple[Node, int, int]:
        """Move current node's right most value to right sibling, key is optional.

        :param node: _description_
        :type node: Node
        :return: node whose minimum key has changed, old minimum key, new minimum key
        :rtype: tuple[Node, int, int]
        """
        logger.debug("Rotate to right")
        right_sibling = node.next

        # old and new minimum key of right sibling
        old_min_key = self._search_min_key_in_subtree(right_sibling.values[0])
        new_min_key = self._search_min_key_in_subtree(node.values[-1])

        # if it's a internal node, move only the rightmost child because it will be
        # in the leftmost position in right sibling, otherwise, also move the key
        # because key = value in external nodes.
        right_sibling.keys.insert(0, new_min_key if node.leaf else old_min_key)
        right_sibling.values.insert(0, node.values[-1])

        node.keys.pop()
        node.values.pop()

        if not right_sibling.leaf:
            right_sibling.values[0].parent = right_sibling
        return right_sibling.parent, old_min_key, new_min_key

    def _left_redistribute(self, node: Node, idx: int) -> tuple[Node, int, int]:
        """Borrow key and value from left sibling or merge with it.

        :param node: node to redistribute
        :type node: Node
        :param idx: index of the node in its parent's child
        :type idx: int
        :raises LeftRedistributeError: raise when distribution is not possible
        :return: node whose minimum key has changed, old minimm key, new minimum key
        :rtype: tuple[Node, int, int]
        """
        left_sibling = node.prev
        if left_sibling is None:
            raise LeftRedistributeError

        # borrow
        if len(left_sibling.keys) > math.ceil(self.order / 2):
            logger.debug("Left borrow")
            return self._right_rotate(left_sibling)

        if len(node.keys) + len(left_sibling.keys) > self.order:
            raise LeftRedistributeError

        # merge
        logger.debug("Left merge")
        old_min_key = self._search_min_key_in_subtree(node.values[0])
        if idx == 0:
            new_min_key = self._search_min_key_in_subtree(node.next.values[0])
        else:
            new_min_key = old_min_key
        merged_keys = node.keys if node.leaf else [old_min_key] + node.keys
        left_sibling.keys.extend(merged_keys)
        left_sibling.values.extend(node.values)

        # remove key and child from direct parent
        key_idx = idx if idx == 0 else idx - 1
        node.parent.keys.pop(key_idx)
        node.parent.values.pop(idx)

        if not node.leaf:
            for child in left_sibling.values:
                child.parent = left_sibling

        # concatenate the doubly linked list
        left_sibling.next = node.next
        if node.next:
            node.next.prev = left_sibling
        return node.parent, old_min_key, new_min_key

    def _right_redistribute(self, node: Node) -> tuple[Node, int, int]:
        """Borrow key and value from right sibling or merge with it.

        :param node: node to redistribute
        :type node: Node
        :return: dummy node and keys.
        :rtype: tuple[Node, int, int]
        """
        # borrow
        right_sibling = node.next
        if len(right_sibling.keys) > math.ceil(self.order / 2):
            logger.debug("Right borrow")
            return self._left_rotate(right_sibling)

        # merge, only happend at left most node
        # if len(node.keys) + len(right_sibling.keys) <= self.order:
        logger.debug("Right merge")
        new_min_key = self._search_min_key_in_subtree(right_sibling.values[0])
        merged_keys = node.keys if node.leaf else node.keys + [new_min_key]
        right_sibling.keys = merged_keys + right_sibling.keys
        right_sibling.values = node.values + right_sibling.values

        node.parent.keys.pop(0)
        node.parent.values.pop(0)

        if not node.leaf:
            for child in right_sibling.values:
                child.parent = right_sibling

        right_sibling.prev = None
        return None, -1, -1

    def _update_parents(self, node: Node, old_min_key: int, new_min_key: int) -> None:
        """Backtrack, replace old minimum keys with new minimum keys until root.

        :param node: base for backtrack
        :type node: Node
        :param old_min_key: old minimum key in node's subtrees
        :type old_min_key: int
        :param new_min_key: new minimum key in node's subtrees
        :type new_min_key: int
        """
        while node:
            try:
                node.keys[node.keys.index(old_min_key)] = new_min_key
            except ValueError:
                pass
            node = node.parent

    def _chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    # ---------------------------------------------------------------------------- #
    #                                  operations                                  #
    # ---------------------------------------------------------------------------- #
    @_display_bplus_tree
    def insert(self, data: int) -> None:
        """Perform insertion on leaf node, rotate, split, and merge it if necessary.

        :param data: data to insert
        :type data: int
        """
        logger.info(f"Insert data: {data}")

        # insert into leaf node
        path = []
        curr_node = self.root
        while not curr_node.leaf:
            curr_node, idx = self._search_position_in_child(curr_node, data)
            path.append(idx)
        curr_node.add(data)

        while curr_node is not None and curr_node.is_overflow():
            try:
                # try rotate first
                self._update_parents(*self._rotate(curr_node))
                return
            except RotateError:
                # split instead, and merge into its parent if there's any
                curr_node.split()
                if curr_node.parent is not None:
                    self._merge_into_parent(curr_node, path.pop())

            curr_node = curr_node.parent

    def insert_without_display(self, data: int) -> None:
        """Insertion without displaying B+ tree content, designed for initialization.

        :param data: data to insert
        :type data: int
        """
        self.insert.__wrapped__(self, data)

    @_display_bplus_tree
    def delete(self, data: int) -> None:
        """Perform deletion on leaf node, redistribute until there's no underflow node.

        :param data: data to delete
        :type data: int
        """
        logger.info(f"Delete data: {data}")

        path = []
        curr_node = self.root
        while not curr_node.leaf:
            curr_node, idx = self._search_position_in_child(curr_node, data)
            path.append(idx)

        try:
            base, old_min_key, new_min_key = curr_node.remove(data)
        except RemoveError:
            return  # lazy return
        self._update_parents(base, old_min_key, new_min_key)

        # loop because current node's parent may underflow if merge happend
        while (
            curr_node is not None
            and curr_node.parent is not None
            and curr_node.is_underflow()
        ):
            try:
                self._update_parents(*self._left_redistribute(curr_node, path.pop()))
            except LeftRedistributeError:
                self._update_parents(*self._right_redistribute(curr_node))

            curr_node = curr_node.parent

        # there may be only one internal and one external node after redistribution
        # if so, promote the only external node to root
        if not self.root.leaf and len(self.root.values) <= 1:
            self.root = self.root.values[0]
            self.root.parent = None

    def display(self) -> None:
        """Print B+ tree in preorder traversal."""
        logger.info("================== Display content of B+ tree ==================")
        self.root.show()
        print("")

    def find(self, data: int) -> None:
        """Search for the given data in external (leaf) node.

        Search for the data based on the keys of internal nodes, then search for the
        exact index in external node.

        :param data: target data
        :type data: int
        """
        curr_node = self.root
        while not curr_node.leaf:
            curr_node, _ = self._search_position_in_child(curr_node, data)

        try:
            curr_node.keys.index(data)
            print(f"Key found: {data}")
        except ValueError:
            print(f"Key not found: {data}")

    # ---------------------------------------------------------------------------- #
    #                                initialization                                #
    # ---------------------------------------------------------------------------- #
    def initialize(self, values: list[int]) -> None:
        """Initialize the B+ tree using sequential insertion.

        :param values: data to insert
        :type values: list[int]
        """
        for value in values:
            self.insert_without_display(value)
        self.display()

    @_display_bplus_tree
    def bulk_load(self, values: list[int]) -> None:
        """Initialize the B+ tree using bulk loading.

        :param values: data to insert
        :type values: list[int]
        """
        self.root.leaf = False
        last_parent = self.root
        left_sibling = None

        buckets = self._chunks(sorted(values), self.order)
        for i, bucket in enumerate(buckets):
            curr_node = Node(
                self.order, True, deepcopy(bucket), deepcopy(bucket), last_parent
            )

            # update doubly linked list
            if left_sibling is not None:
                left_sibling.next = curr_node
            curr_node.prev = left_sibling
            left_sibling = curr_node

            # if it's not the leftmost leaf, append the minimum key in current bucket
            # to the rightmost position of its parent's keys
            if i != 0:
                last_parent.keys.append(bucket[0])
            last_parent.values.append(curr_node)

            first_split = False
            curr_node = last_parent
            while curr_node is not None and curr_node.is_overflow():
                curr_node.split()
                if curr_node.parent is not None:
                    self._merge_into_parent(curr_node, -1)
                # when the first internal node is splitted (first iteration),
                # update last parent to its right child because the last parent is
                # always the lowest and rightmost internal node.
                #           x
                #  o  =>  /   \
                #       x       o
                if not first_split:
                    last_parent = last_parent.values[1]
                    first_split = True

                curr_node = curr_node.parent
