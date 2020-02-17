import pygame
import sys
import os
import csv
import copy
import time
from configuration import COLORS, MAPS
WIDTH = 750
HEIGHT = 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.font.init()
font = pygame.font.Font(None, 35)
FPS = 50
pygame.display.set_caption(f'Snake')
SCREEN_SIZE = (750, 750)
screen = pygame.display.set_mode(SCREEN_SIZE)
TIMER = 11 # Таймер работы змейки
pygame.time.set_timer(TIMER, 175)


def check_data():
    with open('data/data.txt', 'r') as data:
        data = [line.strip() for line in data]
    return data


def terminate(*end_data):
    end_data = [str(i) for i in end_data]
    with open('data/data.txt', 'w') as data:
        for i in end_data:
            data.writelines(i + '\n')
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert_alpha()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Board():
	vector = [0, 1] # Начальный вектор змеи (вправо)

	def __init__(self, map_, skin, width, height):
		self.apples = map_['APPLES']
		self.walls = map_['WALLS']
		self.snake = map_['SNAKE']

		self.skin = skin
		self.width, self.height = (width, height)

		self.set_view()

	def set_view(self, left=0, top=0, cell_size=25): # Тут создается список поля
		self.left = left
		self.top = top
		self.cell_size = cell_size

		cell_data = {'coord_x': None,
					 'coord_y': None,
					 'size': cell_size,
					 'mode': 0}
		self.board = [[cell_data.copy() for _ in range(self.width)]
										for _ in range(self.height)]

	def render(self):
		result = self.move() # Изменение поля
		# Потом все рисуется на экран
		size = self.cell_size
		get_fill = lambda mode: -1 if mode == 0 else 0 # Вместо -1 поставить 1 и будет видно поле
		for counter1 in range(self.height):
			for counter2 in range(self.width):
				cell_data = self.board[counter1][counter2]
				x, y = (cell_data['coord_x'], cell_data['coord_y'])
				mode = cell_data['mode']
				color = self.skin[mode]
				fill = get_fill(mode)
				pygame.draw.rect(screen, color, ((x, y), (size, size)), fill)
		return result

	def move(self): # Функция передвижения
		global running
		self.generate() # Все чистится
		food = False

		for i1, i2 in self.apples: # Рисуется еда
			self.board[i1][i2]['mode'] = 1

		for i1, i2 in self.walls: # Рисуются стены
			self.board[i1][i2]['mode'] = 2

		# Изменение координат в зависимости от вектора
		i1, i2 = self.snake[0]
		i1 += self.vector[0]
		i2 += self.vector[1]

		# Реализация тора
		if i1 >= self.height:
			i1 = 0
		elif i1 <= -1:
			i1 = self.height - 1
		if i2 >= self.width:
			i2 = 0
		elif i2 <= -1:
			i2 = self.height - 1

		if self.board[i1][i2]['mode'] == 1: # Проверка на еду
			food = True
			self.apples.remove([i1, i2])

			if len(self.apples) == 0: # Есть ли еда на поле
				return 'Win'

		if [i1, i2] in self.snake: # Проверка на удар в себя
			return 'Lose'

		if [i1, i2] in self.walls: # Проверка на удар в стену
			return 'Lose'

		# Изменение коодинат башки змейки
		self.snake.insert(0, [i1, i2])
		self.snake = self.snake[::] if food else self.snake[:-1] # Последняя ячейка не удаляется, если змейка сожрала яблоко

		# Рисуется сама змейка
		i1, i2 = self.snake[0]
		self.board[i1][i2]['mode'] = 3
		counter = 0
		for i1, i2 in self.snake[1:]:
			if counter == 0:
				self.board[i1][i2]['mode'] = 4
				counter = 1
			else:
				self.board[i1][i2]['mode'] = 5
				counter = 0


	def generate(self): # Функция чистит поле, после чего на нем все рисуется
		x, y = (self.left, self.top)
		size = self.cell_size
		for counter1 in range(self.height):
			for counter2 in range(self.width):
				self.board[counter1][counter2] = {'coord_x': x,
												  'coord_y': y,
												  'size': size,
												  'mode': 0}
				x += size
			y += size
			x = self.left


class Button():
    def __init__(self, x, y, w, h, text, event, indent, *args):
        self.x, self.y, self.w, self.h, self.rect = x, y, w, h, pygame.rect.Rect(x, y, w, h)
        self.event, self.text, self.indent, self.args = event, text, indent, args

    def draw(self, surface):
        pygame.draw.rect(surface, (0, 255, 0), self.rect)
        string_rendered = font.render(self.text, 1, pygame.Color('white'))
        string_rect = string_rendered.get_rect()
        string_rect.top, string_rect.left = self.y + 10, self.x + self.indent
        screen.blit(string_rendered, string_rect)

    def mouse_press(self, pos):
        if self.rect.collidepoint(pos):
            if self.args:
                self.event(self.args)
            else:
                self.event()
            return 'Pressed'
        return


class Game():
    def __init__(self, data):
        self.money = int(data[0])
        self.fon = data[1]
        self.fon_image = load_image(self.fon)
        self.skin = int(data[2])
        self.complete_levels = int(data[3])
        if data[4] != '[]':
            self.closed_fons = [int(i) for i in data[4][1:-1].split(', ')]
        else:
            self.closed_fons = []
        if data[5] != '[]':
            self.closed_skins = [int(i) for i in data[5][1:-1].split(', ')]
        else:
            self.closed_skins = []
        self.start_screen()

    def start_screen(self):
        intro_text = ["YandexSnake", "", "",
                      "Управление с помощью стрелочек",]

        fon = pygame.transform.scale(self.fon_image, (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = 10
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate(self.money, self.fon, self.skin, self.complete_levels,
                              self.closed_fons, self.closed_skins)
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return self.main_menu()
            pygame.display.flip()
            clock.tick(FPS)

    def main_menu(self):
        fon = pygame.transform.scale(self.fon_image, (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        buttons = [Button(250, 250, 250, 50, 'Начать играть', self.levels, 43),
                   Button(250, 325, 250, 50, 'Рекорды', self.record_menu, 70),
                   Button(250, 400, 250, 50, 'Магазин', self.shop_menu, 75),
                   Button(250, 475, 250, 50, 'Выход', terminate, 80, self.money, self.fon,
                          self.skin, self.complete_levels,
                          self.closed_fons, self.closed_skins)]
        [i.draw(screen) for i in buttons]
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate(self.money, self.fon, self.skin, self.complete_levels,
                              self.closed_fons, self.closed_skins)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    [i.mouse_press(event.pos) for i in buttons]
            pygame.display.flip()
            clock.tick(FPS)

    def record_menu(self):
        fon = pygame.transform.scale(self.fon_image, (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        buttons = [Button(0, 700, 250, 50, 'В главное меню', self.main_menu, 25)]
        [i.draw(screen) for i in buttons]
        text_coord = 100
        with open('data/records.csv', encoding="utf8") as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i in list(reader):
                string_rendered = font.render(f'{i[0]}  -  {i[1]}', 1, pygame.Color('white'))
                intro_rect = string_rendered.get_rect()
                text_coord += 25
                intro_rect.top = text_coord
                intro_rect.x = 250
                text_coord += intro_rect.height
                screen.blit(string_rendered, intro_rect)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate(self.money, self.fon, self.skin, self.complete_levels,
                              self.closed_fons, self.closed_skins)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    [i.mouse_press(event.pos) for i in buttons]
            pygame.display.flip()
            clock.tick(FPS)

    def shop_menu(self):
        fon = pygame.transform.scale(self.fon_image, (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        buttons = [Button(0, 700, 250, 50, 'В главное меню', self.main_menu, 25),
                   Button(125, 125, 250, 50, 'Оригинальная змея', self.change_snake_skin, 8, 0),
                   Button(125, 200, 250, 50, 'Оранж-желтая змея', self.change_snake_skin, 5, 1),
                   Button(125, 275, 250, 50, 'Оранж-белая змея', self.change_snake_skin, 10, 2),
                   Button(400, 125, 250, 50, 'Оригинальный фон', self.change_fon, 3, 'fon.jpg', 0),
                   Button(400, 200, 250, 50, 'Фон с желтой змеей', self.change_fon, 3, 'fon2.jpg', 1),
                   Button(400, 275, 250, 50, 'Фон с красной змеей', self.change_fon, 0, 'fon3.jpg', 2)]
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate(self.money, self.fon, self.skin, self.complete_levels,
                              self.closed_fons, self.closed_skins)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    [i.mouse_press(event.pos) for i in buttons]
            [i.draw(screen) for i in buttons]
            string_rendered = font.render(f'Монет: {self.money}, Все по 5 монет!', 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            intro_rect.top, intro_rect.left = (0, 0)
            screen.blit(string_rendered, intro_rect)
            pygame.display.flip()
            clock.tick(FPS)

    def levels(self):
        fon = pygame.transform.scale(self.fon_image, (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        buttons = [Button(250, 125, 250, 50, '1 уровень', self.starting_level, 70, 0),
                   Button(250, 200, 250, 50, '2 уровень', self.starting_level, 70, 1),
                   Button(250, 275, 250, 50, '3 уровень', self.starting_level, 70, 2),
                   Button(250, 350, 250, 50, '4 уровень', self.starting_level, 70, 3),
                   Button(250, 425, 250, 50, '5 уровень', self.starting_level, 70, 4),
                   Button(250, 500, 250, 50, 'В главное меню', self.main_menu, 25)]
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate(self.money, self.fon, self.skin, self.complete_levels,
                              self.closed_fons, self.closed_skins)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    [i.mouse_press(event.pos) for i in buttons]
            [i.draw(screen) for i in buttons]
            pygame.display.flip()
            clock.tick(FPS)

    def change_snake_skin(self, but_info):
        fon = pygame.transform.scale(self.fon_image, (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        if but_info[0] in self.closed_skins:
            if self.money >= 5:
                self.money -= 5
                string_rendered = font.render('Скин установлен', 1, pygame.Color('white'))
                intro_rect = string_rendered.get_rect()
                intro_rect.top, intro_rect.left = (50, 300)
                screen.blit(string_rendered, intro_rect)
                self.closed_skins.remove(but_info[0])
                self.skin = but_info[0]
            else:
                string_rendered = font.render('Не хватает денег', 1, pygame.Color('white'))
                intro_rect = string_rendered.get_rect()
                intro_rect.top, intro_rect.left = (50, 300)
                screen.blit(string_rendered, intro_rect)
        else:
            self.skin = but_info[0]
            string_rendered = font.render('Скин установлен', 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            intro_rect.top, intro_rect.left = (50, 300)
            screen.blit(string_rendered, intro_rect)

    def change_fon(self, but_info):
        if but_info[1] in self.closed_fons:
            if self.money >= 5:
                self.money -= 5
                self.fon = but_info[0]
                self.fon_image = load_image(self.fon)
                fon = pygame.transform.scale(load_image(self.fon), (WIDTH, HEIGHT))
                screen.blit(fon, (0, 0))
                string_rendered = font.render('Фон установлен', 1, pygame.Color('white'))
                intro_rect = string_rendered.get_rect()
                intro_rect.top, intro_rect.left = (50, 300)
                screen.blit(string_rendered, intro_rect)
                self.closed_fons.remove(but_info[1])
            else:
                string_rendered = font.render('Не хватает денег', 1, pygame.Color('white'))
                intro_rect = string_rendered.get_rect()
                intro_rect.top, intro_rect.left = (50, 300)
                screen.blit(string_rendered, intro_rect)
        else:
            self.fon = but_info[0]
            self.fon_image = load_image(self.fon)
            fon = pygame.transform.scale(load_image(self.fon), (WIDTH, HEIGHT))
            screen.blit(fon, (0, 0))
            string_rendered = font.render('Фон установлен', 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            intro_rect.top, intro_rect.left = (50, 300)
            screen.blit(string_rendered, intro_rect)

    def starting_level(self, but_info):
        if but_info[0] > self.complete_levels:
            string_rendered = font.render('Вы не прошли предидущие уровни!', 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            intro_rect.top, intro_rect.left = (10, 160)
            screen.blit(string_rendered, intro_rect)
        else:
            start = time.time()
            board = Board(copy.deepcopy(MAPS[but_info[0]]), COLORS[self.skin], 30, 30)
            result = None
            flag = True
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        terminate(self.money, self.fon, self.skin, self.complete_levels,
                                  self.closed_fons, self.closed_skins)
                    if event.type == pygame.KEYDOWN:
                        if flag:
                            if event.key == 273 and board.vector != [1, 0]:
                                board.vector = [-1, 0]
                            if event.key == 274 and board.vector != [-1, 0]:
                                board.vector = [1, 0]
                            if event.key == 276 and board.vector != [0, 1]:
                                board.vector = [0, -1]
                            if event.key == 275 and board.vector != [0, -1]:
                                board.vector = [0, 1]
                        if event.key == pygame.K_t:
                            flag = False if flag else True
                        if event.key == pygame.K_r:
                            return self.starting_level(but_info)
                        if event.key == pygame.K_n:
                            result = 'Win'
                    if event.type == TIMER:
                        if flag:
                            screen.fill(pygame.Color('black'))
                            result = board.render()
                            pygame.display.flip()
                if result:
                    return self.gameover(result, round(time.time() - start, 2), but_info[0])

    def gameover(self, result, time, level):
        if result == 'Lose':
            image = load_image('gameover.png')
        else:
            image = load_image('youwin.png')
            self.complete_levels += 1
            self.money += 5
            with open('data/records.csv', encoding="utf8") as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                records = list(reader)
                if float(records[level][1]) > time:
                    records[level][1] = time
            with open('data/records.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='"')
                for row in records:
                    writer.writerow(row)
        screen.blit(image, (0, 0))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate(self.money, self.fon, self.skin, self.complete_levels,
                              self.closed_fons, self.closed_skins)
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return self.main_menu()
            pygame.display.flip()
            clock.tick(FPS)


if __name__ == "__main__":
    Game(check_data())