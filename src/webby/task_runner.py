import threading


class SingleThreadedTaskRunner:
    def __init__(self, tab):
        self.tab = tab
        self.needs_quit = False
        self.tasks = []

    def schedule_task(self, callback):
        self.tasks.append(callback)
        self.tab.browser.needs_animation_frame = True

    def run_tasks(self):
        while self.tasks:
            task = self.tasks.pop(0)
            task.run()

    def clear_pending_tasks(self):
        self.tasks = []

    def start_thread(self):
        pass

    def set_needs_quit(self):
        self.needs_quit = True
        pass

    def run(self):
        pass


class CommitData:
    def __init__(self, url, scroll, height, display_list):
        self.url = url
        self.scroll = scroll
        self.height = height
        self.display_list = display_list


class TaskRunner:
    def __init__(self, tab):
        self.condition = threading.Condition()
        self.tab = tab
        self.tasks = []
        self.main_thread = threading.Thread(
            target=self.run,
            name="Main thread",
        )
        self.needs_quit = False

    def schedule_task(self, task):
        self.condition.acquire(blocking=True)
        self.tasks.append(task)
        self.condition.notify_all()
        self.condition.release()

    def set_needs_quit(self):
        self.condition.acquire(blocking=True)
        self.needs_quit = True
        self.condition.notify_all()
        self.condition.release()

    def clear_pending_tasks(self):
        self.condition.acquire(blocking=True)
        self.tasks.clear()
        self.condition.release()

    def start_thread(self):
        self.main_thread.start()

    def run(self):
        while True:
            self.condition.acquire(blocking=True)
            needs_quit = self.needs_quit
            self.condition.release()
            if needs_quit:
                self.handle_quit()
                return

            task = None
            self.condition.acquire(blocking=True)
            if len(self.tasks) > 0:
                task = self.tasks.pop(0)
            self.condition.release()
            if task:
                task.run()

            self.condition.acquire(blocking=True)
            if len(self.tasks) == 0 and not self.needs_quit:
                self.condition.wait()
            self.condition.release()

    def handle_quit(self):
        pass
