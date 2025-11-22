import os

import spade
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour

from fish import Fish

fishes: list[Fish] = []


def fish2dict(fish):
    return {
        "x": fish.x,
        "y": fish.y,
        "size": fish.size,
        "color": fish.color,
    }


class HostAgent(Agent):
    class FishUpdaterBehaviour(PeriodicBehaviour):
        counter = 0

        async def on_start(self):
            print(f"Agente corre cada {self.period} segundos")
            self.counter = 0

        async def run(self):
            self.counter += 1
            if self.counter % 20 == 0:
                self.counter = 0
                print(f"Fishes swimming. Look a fish! {fishes[0].__dict__}")

            for fish in fishes:
                fish.defineStatus()
                fish.nadar()

    class CenterUpdaterBehaviour(PeriodicBehaviour):
        async def on_start(self) -> None:
            self.agent.x_center = 0

        async def run(self) -> None:
            self.agent.x_center += 5

    async def setup(self):
        print(f"Agente {self.jid} started...")
        for _ in range(1000):
            fishes.append(Fish(1500, 900, self))
        self.x_center = 0

        self.add_behaviour(self.FishUpdaterBehaviour(period=0.2))
        self.add_behaviour(self.CenterUpdaterBehaviour(period=1))

        print("Host agent started!")


async def main():
    host = HostAgent("z3r007@xmpp.jp", "12356890")
    await host.start()

    async def fishes_controller(_):
        return [fish2dict(fish) for fish in fishes]

    host.web.add_get("/fishes", fishes_controller, template=None)
    host.web.start(port=10000)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_folder = os.path.join(base_dir, "static")
    host.web.app.router.add_static("/static/", path=static_folder, name="static")

    print("Agents launched...")
    await spade.wait_until_finished(host)


if __name__ == "__main__":
    spade.run(main())
