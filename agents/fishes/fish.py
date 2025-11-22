import random


class Fish:
    def __init__(self, width, height, parent):
        self.worldWidth = width
        self.worldHeight = height
        self.parent = parent
        self.status = 1
        self.x = random.randint(10, width)
        self.y = random.randint(10, height)
        self.color = 0xFF0000 + (random.randint(0, 255) << 8)
        self.size = random.randint(5, 20)
        self.speed = 250 / self.size

    def defineStatus(self):
        # 1:vigilar,2:comer,3:subir,4:bajar
        if self.y < self.worldHeight * 0.2:
            self.status = 1
            if self.x > 100 + self.parent.x_center:
                self.status = 4
        elif self.y >= self.worldHeight * 0.8:
            self.status = 2
            if self.x < 30 + self.parent.x_center:
                self.status = 3
        else:
            if self.x < 30 + self.parent.x_center:
                self.status = 3
            else:
                self.status = 4

    def nadar(self):
        match self.status:
            case 1:
                self.x += self.speed
            case 2:
                self.x -= self.speed
            case 3:
                self.y -= self.speed
            case 4:
                self.y += self.speed

