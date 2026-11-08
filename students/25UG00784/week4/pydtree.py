"""
PyDTree -- Build an Adaptive 20-Questions Engine
Week 4 | Trees

Standard library only (json, sys, typing).

Run tests : python pydtree.py --test
Play mode : python pydtree.py
"""

import json
import sys
from typing import Any, Dict, List, Optional

SAVE_FILE = "pydtree_knowledge.json"


# ---------------------------------------------------------------------------
# Milestone 1: The Decision Tree Node
# ---------------------------------------------------------------------------
class TreeNode:
    def __init__(self, text: str, yes_child=None, no_child=None):
        self.text = text.strip()
        self.yes_child = yes_child
        self.no_child = no_child

    def is_leaf(self) -> bool:
        """Returns True if this node has no children (it's a final guess)."""
        return self.yes_child is None and self.no_child is None


# ---------------------------------------------------------------------------
# Milestone 2: Recursive Metrics
# ---------------------------------------------------------------------------
def count_nodes(root: Optional[TreeNode]) -> int:
    if root is None:
        return 0
    return 1 + count_nodes(root.yes_child) + count_nodes(root.no_child)


def count_leaves(root: Optional[TreeNode]) -> int:
    if root is None:
        return 0
    if root.is_leaf():
        return 1
    return count_leaves(root.yes_child) + count_leaves(root.no_child)


def tree_height(root: Optional[TreeNode]) -> int:
    if root is None:
        return -1
    if root.is_leaf():
        return 0
    return 1 + max(tree_height(root.yes_child), tree_height(root.no_child))


# ---------------------------------------------------------------------------
# Milestone 3: The 3 Great Recursive Walks
# (yes_child is treated as "left", no_child as "right")
# ---------------------------------------------------------------------------
def preorder_traversal(root: Optional[TreeNode]) -> List[str]:
    if root is None:
        return []
    return ([root.text]
            + preorder_traversal(root.yes_child)
            + preorder_traversal(root.no_child))


def inorder_traversal(root: Optional[TreeNode]) -> List[str]:
    if root is None:
        return []
    return (inorder_traversal(root.yes_child)
            + [root.text]
            + inorder_traversal(root.no_child))


def postorder_traversal(root: Optional[TreeNode]) -> List[str]:
    if root is None:
        return []
    return (postorder_traversal(root.yes_child)
            + postorder_traversal(root.no_child)
            + [root.text])


# ---------------------------------------------------------------------------
# Milestone 4: Knowledge Tree Serialization
# ---------------------------------------------------------------------------
def tree_to_dict(root: Optional[TreeNode]) -> Optional[Dict[str, Any]]:
    if root is None:
        return None
    if root.is_leaf():
        return {"guess": root.text}
    return {
        "question": root.text,
        "yes": tree_to_dict(root.yes_child),
        "no": tree_to_dict(root.no_child),
    }


def dict_to_tree(data: Optional[Dict[str, Any]]) -> Optional[TreeNode]:
    if data is None:
        return None
    if "guess" in data:
        return TreeNode(data["guess"])
    return TreeNode(
        data["question"],
        dict_to_tree(data.get("yes")),
        dict_to_tree(data.get("no")),
    )


# ---------------------------------------------------------------------------
# Milestone 5: The Magic of Pointer Grafting
# ---------------------------------------------------------------------------
def graft_new_knowledge(
    leaf_node: TreeNode,
    new_question: str,
    new_guess: str,
    new_guess_is_yes: bool,
) -> None:
    """Transform a wrongly-guessed leaf into a question node, in place."""
    old_guess = leaf_node.text                      # 1. remember old guess
    new_leaf = TreeNode(new_guess)                  # 2. two new leaves
    old_leaf = TreeNode(old_guess)
    leaf_node.text = new_question.strip()           # 3. mutate into question
    if new_guess_is_yes:                            # 4. hook the children
        leaf_node.yes_child = new_leaf
        leaf_node.no_child = old_leaf
    else:
        leaf_node.yes_child = old_leaf
        leaf_node.no_child = new_leaf


# ---------------------------------------------------------------------------
# Default seed
# ---------------------------------------------------------------------------
def build_default_tree() -> TreeNode:
    return TreeNode(
        "Does it live in water?",
        TreeNode("Dolphin"),
        TreeNode(
            "Does it bark?",
            TreeNode("Dog"),
            TreeNode("Elephant"),
        ),
    )


# ---------------------------------------------------------------------------
# Milestone 6: ASCII Visualizer & Interactive REPL
# ---------------------------------------------------------------------------
def _label(node: TreeNode) -> str:
    return ("[*] " if False else ("[\u2605] " if node.is_leaf() else "[?] ")) + node.text


def _ascii_lines(node: TreeNode, prefix: str, lines: List[str]) -> None:
    children = [("Yes", node.yes_child), ("No", node.no_child)]
    children = [(tag, c) for tag, c in children if c is not None]
    for i, (tag, child) in enumerate(children):
        last = i == len(children) - 1
        connector = "\u2514\u2500" if last else "\u251c\u2500"
        lines.append(f"{prefix}{connector} ({tag}) {_label(child)}")
        _ascii_lines(child, prefix + ("   " if last else "\u2502  "), lines)


def build_ascii_tree(root: Optional[TreeNode]) -> str:
    if root is None:
        return "(empty tree)"
    lines = [_label(root)]
    _ascii_lines(root, "", lines)
    return "\n".join(lines)


def print_ascii_tree(root: Optional[TreeNode]) -> None:
    """Draws a branching ASCII hierarchy: questions [?], guesses [star]."""
    print(build_ascii_tree(root))


class MindReaderEngine:
    def __init__(self, save_file: str = SAVE_FILE):
        self.save_file = save_file
        self.root = self._load()

    # ---- persistence ----
    def _load(self) -> TreeNode:
        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                return dict_to_tree(json.load(f))
        except (OSError, ValueError, KeyError, TypeError):
            return build_default_tree()

    def _save(self) -> None:
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(tree_to_dict(self.root), f, indent=2)
        except OSError:
            print("(Could not save knowledge to disk.)")

    # ---- input helpers ----
    @staticmethod
    def _ask(prompt: str) -> str:
        try:
            return input(prompt).strip()
        except EOFError:
            print()
            return ""

    def _ask_yes_no(self, prompt: str) -> bool:
        while True:
            ans = self._ask(prompt + " (y/n): ").lower()
            if ans in ("y", "yes"):
                return True
            if ans in ("n", "no"):
                return False
            print("Please answer 'y' or 'n'.")

    # ---- game ----
    def play(self) -> None:
        print("\nThink of an animal, thing or character... I'll try to guess it!")
        node = self.root
        while not node.is_leaf():
            answer = self._ask_yes_no(node.text)
            node = node.yes_child if answer else node.no_child

        if self._ask_yes_no(f"Is it a/an {node.text}?"):
            print("I win! Got it right again.")
            return

        print("I give up! Help me learn.")
        new_guess = self._ask("What were you thinking of? ")
        if not new_guess:
            print("No answer given, nothing learned.")
            return
        new_question = self._ask(
            f"Give me a yes/no question that tells a {new_guess} "
            f"from a {node.text}: ")
        if not new_question:
            print("No question given, nothing learned.")
            return
        is_yes = self._ask_yes_no(f"For a {new_guess}, the answer is")
        graft_new_knowledge(node, new_question, new_guess, is_yes)
        self._save()
        print(f"Thanks! I've learned about '{new_guess}'.")

    def show_tree(self) -> None:
        print()
        print_ascii_tree(self.root)

    def show_analytics(self) -> None:
        print("\n--- Tree Analytics ---")
        print(f"Height      : {tree_height(self.root)}")
        print(f"Leaves      : {count_leaves(self.root)}")
        print(f"Total nodes : {count_nodes(self.root)}")

    def show_traversals(self) -> None:
        print("\n--- Traversals ---")
        print("Pre-order :", preorder_traversal(self.root))
        print("In-order  :", inorder_traversal(self.root))
        print("Post-order:", postorder_traversal(self.root))

    def reset(self) -> None:
        self.root = build_default_tree()
        self._save()
        print("Knowledge reset to the default seed.")

    def run(self) -> None:
        menu = (
            "\n=== PyDTree Mind Reader ===\n"
            "1. Play 20-Questions\n"
            "2. Display Visual Tree\n"
            "3. View Tree Analytics\n"
            "4. View Traversals\n"
            "5. Reset to default seed\n"
            "6. Exit"
        )
        while True:
            print(menu)
            try:
                choice = input("Choose an option: ").strip()
            except EOFError:
                print()
                break
            if choice == "1":
                self.play()
            elif choice == "2":
                self.show_tree()
            elif choice == "3":
                self.show_analytics()
            elif choice == "4":
                self.show_traversals()
            elif choice == "5":
                self.reset()
            elif choice == "6":
                print("Goodbye!")
                break
            else:
                print("Invalid choice, enter a number from 1 to 6.")


# ---------------------------------------------------------------------------
# Self-Verification Test Suite
# ---------------------------------------------------------------------------
def run_tests() -> None:
    bar = "=" * 60
    print(bar)
    print("\U0001F9EA Running PyDTree Milestone Verification Test Suite...")
    print(bar)

    # Test 1: Node & leaf properties
    n = TreeNode("  Dog  ")
    assert n.text == "Dog"
    assert n.yes_child is None and n.no_child is None
    assert n.is_leaf() is True
    parent = TreeNode("Q?", TreeNode("A"), TreeNode("B"))
    assert parent.is_leaf() is False
    print("  \u2713 Test 1: Node & Leaf properties verified.")

    # Test 2: Boundary edge cases
    assert count_nodes(None) == 0
    assert count_leaves(None) == 0
    assert tree_height(None) == -1
    single = TreeNode("Solo")
    assert count_nodes(single) == 1
    assert count_leaves(single) == 1
    assert tree_height(single) == 0
    assert preorder_traversal(None) == []
    assert inorder_traversal(None) == []
    assert postorder_traversal(None) == []
    print("  \u2713 Test 2: Boundary edge cases (None, single node) verified.")

    # Test 3: Metrics on multi-level tree
    tree = build_default_tree()
    assert count_nodes(tree) == 5
    assert count_leaves(tree) == 3
    assert tree_height(tree) == 2
    print("  \u2713 Test 3: Metrics on multi-level tree verified.")

    # Test 4: Traversals
    assert preorder_traversal(tree) == [
        "Does it live in water?", "Dolphin", "Does it bark?", "Dog", "Elephant"]
    assert inorder_traversal(tree) == [
        "Dolphin", "Does it live in water?", "Dog", "Does it bark?", "Elephant"]
    assert postorder_traversal(tree) == [
        "Dolphin", "Dog", "Elephant", "Does it bark?", "Does it live in water?"]
    print("  \u2713 Test 4: Pre-order, In-order, Post-order walks verified.")

    # Test 5: Dynamic pointer mutation
    t = build_default_tree()
    elephant = t.no_child.no_child
    graft_new_knowledge(elephant, "Does it have wings?", "Eagle", True)
    assert elephant.text == "Does it have wings?"
    assert elephant.yes_child.text == "Eagle" and elephant.yes_child.is_leaf()
    assert elephant.no_child.text == "Elephant" and elephant.no_child.is_leaf()
    assert count_nodes(t) == 7 and count_leaves(t) == 4 and tree_height(t) == 3
    dog = t.no_child.yes_child
    graft_new_knowledge(dog, "Is it a reptile?", "Lizard", False)
    assert dog.yes_child.text == "Dog" and dog.no_child.text == "Lizard"
    print("  \u2713 Test 5: Dynamic Pointer Mutation (Knowledge Grafting) verified.")

    # Test 6: JSON round trip
    d = tree_to_dict(t)
    assert tree_to_dict(None) is None
    assert tree_to_dict(TreeNode("X")) == {"guess": "X"}
    restored = dict_to_tree(json.loads(json.dumps(d)))
    assert tree_to_dict(restored) == d
    assert preorder_traversal(restored) == preorder_traversal(t)
    assert dict_to_tree(None) is None
    print("  \u2713 Test 6: JSON Dictionary serialization round-trip verified.")

    # Test 7: Default seed
    seed = build_default_tree()
    assert seed.text == "Does it live in water?"
    assert seed.yes_child.text == "Dolphin"
    assert seed.no_child.text == "Does it bark?"
    assert seed.no_child.yes_child.text == "Dog"
    assert seed.no_child.no_child.text == "Elephant"
    print("  \u2713 Test 7: Default seed knowledge tree verified.")

    print()
    print(bar)
    print("\U0001F389 ALL 7 ASSIGNMENT UNIT TESTS PASSED! SCORE: 100/100")
    print(bar)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # emoji / box characters on Windows
    except (AttributeError, ValueError):
        pass
    if "--test" in sys.argv:
        try:
            run_tests()
        except AssertionError:
            print("A test failed.")
            sys.exit(1)
        return
    MindReaderEngine().run()


if __name__ == "__main__":
    main()