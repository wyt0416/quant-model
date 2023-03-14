from qtmodel.discretizedasset import DiscretizedAsset
from qtmodel.error import QTError
from qtmodel.exercise import ExerciseTypes
from qtmodel.option import OptionArguments
from qtmodel.stochasticprocess import StochasticProcess
from qtmodel.timegrid import TimeGrid


class DiscretizedVanillaOption(DiscretizedAsset):

    def __init__(self,
                 args: OptionArguments,
                 process: StochasticProcess,
                 grid: TimeGrid):
        super(DiscretizedVanillaOption, self).__init__()
        self._arguments = args
        self._stopping_times = [None] * len(args.exercise.dates())
        for i in range(len(self._stopping_times)):
            self._stopping_times[i] = process.time(args.exercise.date(i))
            if not grid.empty():
                # adjust to the given grid
                self._stopping_times[i] = grid.closest_time(self._stopping_times[i])

    def reset(self, size: int):
        self._values = [0.0] * size
        self.adjust_values()

    def mandatory_times(self):
        return self._stopping_times

    def post_adjust_values_impl(self):
        now = self.time()
        if self._arguments.exercise.type() == ExerciseTypes.American:
            if self._stopping_times[1] >= now >= self._stopping_times[0]:
                self.apply_specific_condition()
        elif self._arguments.exercise.type() == ExerciseTypes.European:
            if self.is_on_time(self._stopping_times[0]):
                self.apply_specific_condition()
        elif self._arguments.exercise.type() == ExerciseTypes.Bermudan:
            for stopping_time in self._stopping_times:
                if self.is_on_time(stopping_time):
                    self.apply_specific_condition()
        else:
            QTError("invalid option type")

    def apply_specific_condition(self):
        grid = self.method().grid(self.time())
        for j in range(len(self._values)):
            self._values[j] = max(self._values[j], self._arguments.payoff(grid[j]))
