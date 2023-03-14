

class IO:

    @staticmethod
    def ordinal(n: int):
        out = f"{n}"
        if n == 11 or n == 12 or n == 13:
            out += "th"
        else:
            remainder = n % 10
            if remainder == 1:
                out += "st"
            elif remainder == 2:
                out += "nd"
            elif remainder == 3:
                out += "rd"
            else:
                out += "th"

        return out


if __name__ == "__main__":
    print(IO.ordinal(21))