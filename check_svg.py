#!/usr/bin/python3

import argparse
import xml.etree.ElementTree as ET
import readline
import subprocess
from termcolor import colored


class ISpellWrapper(object):

    def __init__(self):
        self._process = subprocess.Popen(["ispell"],
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         bufsize=0)
        self.start_line = self._process.stdout.readline()

    def check(self, word):
        self._process.stdin.write(bytearray(word, encoding='utf-8') + b"\n")
        self._process.stdin.flush()

        result = self._process.stdout.readline()
        correct = True
        while result != b'\n' and result != b'word: \n':
            correct &= result.startswith(
                b'word: ok') or result.startswith(b'ok')
            result = self._process.stdout.readline()

        return correct


def cli_input_with_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input(prompt)
    readline.set_pre_input_hook()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    args = parser.parse_args()
    checker = ISpellWrapper()

    print("-------------------------------------------------------------------")
    print("Spellchecking '{}'".format(colored(args.file, attrs=["bold"])))
    print("Using {}".format(checker.start_line))
    print("-------------------------------------------------------------------")
    print("")

    tree = ET.parse(args.file)
    text_nodes = tree.getroot().findall('.//{http://www.w3.org/2000/svg}tspan')

    num_changes = 0
    for node in text_nodes:
        if node.text is not None:
            words = node.text.split(" ")
            colored_words = []
            contains_error = False
            for word in words:
                if checker.check(word):
                    colored_words.append(word)
                else:
                    colored_words.append(colored(word, color='red'))
                    contains_error = True
            if contains_error:
                print(colored("original:  ", color="yellow") +
                      " ".join(colored_words))
                corrected = cli_input_with_prefill(
                    colored("corrected: ", color="yellow"), node.text)
                if node.text != corrected:
                    node.text = corrected
                    num_changes += 1
                print("")

    if num_changes > 0:
        tree.write(args.file)
        print("Corrected {} strings, saved to {}.".format(num_changes, args.file))
    else:
        print("No changes have been made in {}.".format(args.file))


if __name__ == "__main__":
    main()
