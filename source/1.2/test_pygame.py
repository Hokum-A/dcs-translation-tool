import pygame
import os

def test_zero_byte():
    print("Testing zero byte load")
    pygame.mixer.init()
    with open("empty.wav", "wb") as f:
        pass
    try:
        sound = pygame.mixer.Sound("empty.wav")
        print("Loaded sound")
    except Exception as e:
        print(f"Sound error: {e}")
        
    try:
        pygame.mixer.music.load("empty.wav")
        print("Loaded music")
    except Exception as e:
        print(f"Music error: {e}")

test_zero_byte()
