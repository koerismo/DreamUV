from time import perf_counter, sleep

def print_time_s(t: float) -> str:
    if t < 1.0: return str(round(t * 1000, 2)) + 'ms'
    if t < 60.0: return str(round(t, 2)) + 's'
    if t < 3600.0: return str(round(t / 60, 2)) + 'm'
    return str(round(t / 60 / 60, 2)) + 'h'

def print_percent(t: float) -> str:
    return str(round(t, 2) * 100.0) + '%'

class Profiler():
    name: str
    marker_times: dict[str, float]
    current_time: float = 0.0

    def __init__(self, *args: str, name: str='main') -> None:
        self.name = name
        self.marker_times = {}
        for arg in args:
            self.add_marker(arg)

    def add_marker(self, m: str) -> None:
        self.marker_times[m] = 0.0;

    def clear(self) -> None:
        for m in self.marker_times:
            self.marker_times[m] = 0.0
        self.begin()
    
    def begin(self) -> None:
        self.current_time = perf_counter()

    def marker(self, m: str) -> None:
        new_time = perf_counter()
        self.marker_times[m] += (new_time - self.current_time)
        self.current_time = new_time

    def __str__(self) -> str:
        desired_width = max([len(m) for m in self.marker_times])
        total_time = sum(self.marker_times.values())

        return '\n'.join([
            f'Profiler ({self.name}) results:',
            '------------------------------------',
            *[f'{m}:  {" " * (desired_width - len(m))}{print_time_s(self.marker_times[m])} \t({print_percent(self.marker_times[m] / total_time)})' for m in self.marker_times],
            '------------------------------------'
        ])

if __name__ == '__main__':
    abc = Profiler(
        'a',
        'b',
        'c',
        name='test-profiler'
    )

    abc.add_marker('hello')
    abc.add_marker('bkajhdskhj')

    abc.begin()
    sleep(0.05)
    abc.marker('hello')
    sleep(1.2)
    abc.marker('bkajhdskhj')

    print(abc)
