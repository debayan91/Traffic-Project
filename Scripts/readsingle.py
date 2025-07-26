import time
import os
from pyfirmata2 import ArduinoMega
import pygame

# Arduino Setup
board = ArduinoMega("/dev/tty.usbserial-130")
RED, YELLOW, GREEN = 22, 23, 24

# Initialize pins
for pin in [RED, YELLOW, GREEN]:
    board.digital[pin].mode = 1
    board.digital[pin].write(0)

def set_leds(red, yellow, green):
    board.digital[RED].write(red)
    board.digital[YELLOW].write(yellow)
    board.digital[GREEN].write(green)

def get_latest_delay():
    """Get most recent delay with timestamp checking"""
    try:
        with open('/Users/debayan/Documents/donkey/delays.txt', 'r') as f:
            data = f.read().split()
            # Get all entries after "start"
            entries = [e for e in data if ':' in e]
            if not entries:
                return 5  # Default
            
            # Get newest entry
            newest = entries[-1].split(':')
            timestamp = float(newest[0])
            delay = int(newest[1])
            
            # Only use if recent (last 2 seconds)
            if time.time() - timestamp <= 2:
                return max(3, min(60, delay))  # Clamp between 3-60s
    except:
        pass
    return 5  # Fallback

def main():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    font = pygame.font.Font(None, 36)
    
    current_state = "red"
    next_change = time.time()
    current_delay = 5
    
    set_leds(1, 0, 0)  # Start with red
    
    try:
        while True:
            # Check for quit event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt
            
            # Update delay from file
            new_delay = get_latest_delay()
            if new_delay != current_delay and current_state == "green":
                # Adjust remaining green time
                next_change = time.time() + new_delay
                current_delay = new_delay
            
            # State machine
            now = time.time()
            if now >= next_change:
                if current_state == "red":
                    current_state = "green"
                    current_delay = get_latest_delay()
                    next_change = now + current_delay
                    set_leds(0, 0, 1)
                elif current_state == "green":
                    current_state = "yellow"
                    next_change = now + 3  # Fixed 3s yellow
                    set_leds(0, 1, 0)
                else:  # yellow
                    current_state = "red"
                    next_change = now + 1  # Brief red
                    set_leds(1, 0, 0)
            
            # Display
            screen.fill((0, 0, 0))
            state_text = font.render(f"State: {current_state}", True, (255,255,255))
            time_left = max(0, int(next_change - now))
            time_text = font.render(f"Time left: {time_left}s", True, (255,255,255))
            delay_text = font.render(f"Current Delay: {current_delay}s", True, (255,255,255))
            
            screen.blit(state_text, (50, 50))
            screen.blit(time_text, (50, 100))
            screen.blit(delay_text, (50, 150))
            pygame.display.flip()
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        set_leds(0, 0, 0)
        board.exit()
        pygame.quit()

if __name__ == "__main__":
    main()