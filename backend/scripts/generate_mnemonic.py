#!/usr/bin/env python3
"""Generate a BIP39 mnemonic for the Cashu wallet.

Usage:
    python scripts/generate_mnemonic.py           # 12 words (128 bits)
    python scripts/generate_mnemonic.py --24      # 24 words (256 bits)
    python scripts/generate_mnemonic.py --words 24
"""

import argparse
import sys

from mnemonic import Mnemonic


def generate_mnemonic(word_count: int = 12) -> str:
    """Generate a BIP39 mnemonic with the specified word count.

    Args:
        word_count: Number of words (12 or 24)

    Returns:
        The generated mnemonic phrase
    """
    if word_count not in (12, 24):
        raise ValueError("Word count must be 12 or 24")

    # 12 words = 128 bits, 24 words = 256 bits
    strength = 128 if word_count == 12 else 256

    m = Mnemonic("english")
    return m.generate(strength=strength)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a BIP39 mnemonic for the Cashu wallet"
    )
    parser.add_argument(
        "--words", "-w",
        type=int,
        choices=[12, 24],
        default=12,
        help="Number of words (12 or 24, default: 12)"
    )
    parser.add_argument(
        "--24",
        dest="use_24",
        action="store_true",
        help="Use 24 words (shorthand for --words 24)"
    )

    args = parser.parse_args()

    word_count = 24 if args.use_24 else args.words
    mnemonic = generate_mnemonic(word_count)

    print("\n" + "=" * 60)
    print("Generated BIP39 Mnemonic ({} words)".format(word_count))
    print("=" * 60)
    print()
    print(mnemonic)
    print()
    print("=" * 60)
    print("IMPORTANT: Store this mnemonic securely!")
    print("Add to your .env file as:")
    print()
    print('WALLET_MNEMONIC="{}"'.format(mnemonic))
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
