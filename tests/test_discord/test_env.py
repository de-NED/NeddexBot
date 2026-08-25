import sys
import discord

def test_environment():
    print("PYTHON:", sys.executable)
    print("DISCORD:", discord.__file__)