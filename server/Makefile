# Compiler
CC = gcc

# Flags
CFLAGS = -Wall -g
LDFLAGS = -ljson-c -lws2_32

# Target
TARGET = server

# Source files
SRC = server.c

# Build rule
$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

# Clean rule
clean:
	rm -f $(TARGET)
