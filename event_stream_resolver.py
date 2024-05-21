class EventStreamResolver:
    def __init__(self):
        self.__buffer = ""

    def buffer(self, text: str):
        self.__buffer += text

    def get_messages(self):
        lines = []
        while "\n\n" in self.__buffer:
            message, self.__buffer = self.__buffer.split("\n\n", 1)
            lines.append(message)
        return lines
