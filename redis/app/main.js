const net = require("net");

function isRespArray(string) {
  return string.startsWith("*");
}

function parseRespArray(string) {
  let currentIndex = 1;

  while (string[currentIndex] !== "\r") {
    currentIndex++;
  }

  const parsedArrayElements = [];
  const arrayLength = parseInt(string.substring(1, currentIndex));
  currentIndex += 2;
  for (let i = 0; i < arrayLength; i++) {
    const startIndex = currentIndex;
    while (string[currentIndex] !== "\r") {
      currentIndex++;
    }

    const elementLength = parseInt(
      string.substring(startIndex + 1, currentIndex)
    );

    parsedArrayElements.push(
      string.substring(currentIndex + 2, currentIndex + 2 + elementLength)
    );

    currentIndex += 4 + elementLength;
  }

  return parsedArrayElements;
}

const hashmap = {};

const server = net.createServer((connection) => {
  connection.on("data", (data) => {
    const strinigifiedData = data.toString();
    if (isRespArray(strinigifiedData)) {
      const [command, ...args] = parseRespArray(strinigifiedData);

      switch (command) {
        case "echo":
          connection.write(`+${args[0]}\r\n`);
          break;
        case "ping":
          connection.write("+PONG\r\n");
          break;
        case "set":
          if (args[2] === "px") {
            const ttl = parseInt(args[3]);
            hashmap[args[0]] = {
              value: args[1],
              expiresAt: Date.now() + ttl,
            };
          } else {
            hashmap[args[0]] = {
              value: args[1],
              ttl: undefined,
            };
          }

          connection.write("+OK\r\n");

          break;
        case "get":
          const result = hashmap[args[0]];

          if (result.expiresAt && result.expiresAt < Date.now()) {
            delete hashmap[args[0]];
            connection.write("$-1\r\n");
          } else if (result.value) {
            connection.write(`$${result.value.length}\r\n${result.value}\r\n`);
          } else {
            connection.write("$-1\r\n");
          }

          break;
        default:
          connection.write("-ERR unknown command\r\n");
      }
    } else {
      connection.write("-ERR Protocol error\r\n");
    }
  });
});

server.listen(6379, "127.0.0.1");
