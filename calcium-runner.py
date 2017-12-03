# coding: utf-8

import sys
from calcium.get_terminal_size import get_terminal_size as GTS
import calcium.terminal as terminal
import calcium.image as image
import calcium.core as core


class DigitsSheet:
    frames = image.ImageSprite.get_frames_from_sheet('numbers.png', 10, 1)
    @staticmethod
    def get_text_sprites(number, x, y):
        sprites = list()
        last_x = x
        for i, c in enumerate(str(number)):
            sprite = core.CalciumSprite(
                last_x, y,
                {'normal': [DigitsSheet.frames[int(c)]]})
            sprites.append(sprite)
            last_x += 4
        return sprites


class Timer:
    def __init__(self):
        self.__schedule_funcs = dict()

    def after(self, frames, func):
        self.__schedule_funcs[func] = frames

    def process(self):
        to_delete = list()
        to_run = list()
        for k, v in self.__schedule_funcs.items():
            if v == 0:
                to_run.append(k)
                to_delete.append(k)
            else:
                self.__schedule_funcs[k] -= 1
        # we need to delete the functions before
        # run the functions for situation in which
        # the function call .after scheduling
        # it self
        for k in to_delete:
            del self.__schedule_funcs[k]
        for func in to_run:
            func()


class Scene:
    def __init__(self, terminal):
        self.terminal = terminal
        self.items = list()
        self.timer = Timer()

    def add(self, item):
        self.items.append(item)

    def remove(self, item):
        self.items.remove(item)

    def draw(self):
        self.timer.process()
        self.terminal.screen.clear()
        for item in self.items:
            self.terminal.screen.plot(item)


class CalciumLogoScene(Scene):
    def __init__(self, terminal):
        super(CalciumLogoScene, self).__init__(terminal)
        self.logo = core.CalciumSprite(
            0, 0,
            {'normal': [image.ImageSprite.get_frame_from_image_path('calcium-logo.png')]})
        self.logo.align(
            (0.5, 0.5),
            self.terminal.screen.width / 2,
            self.terminal.screen.height / 2)
        self.add(self.logo)


class GameScene(Scene):
    WALKING = 1
    JUMP_UP = 2
    JUMP_DOWN = 3
    def __init__(self, terminal):
        self.playing = False
        self.character_state = GameScene.WALKING
        super(GameScene, self).__init__(terminal)
        self.character = core.CalciumSprite(
            10, self.terminal.screen.height - 7,
            dict(
                normal=image.ImageSprite.get_frames_from_gif(
                    'character.gif')))
        self.ground_01 = core.CalciumSprite(
            0, self.terminal.screen.height - 1,
            dict(
                normal=[image.ImageSprite.get_frame_from_image_path(
                    'ground.png')]))
        self.obstacle = core.CalciumSprite(
            70, self.terminal.screen.height - 8,
            dict(
                normal=[image.ImageSprite.get_frame_from_image_path(
                    'obstacle-01.png')]))
        self.gameover = core.CalciumSprite(
            0, 0,
            {'normal': [image.ImageSprite.get_frame_from_image_path('game-over.png')]},
            visible=False)
        self.gameover.align(
            (0.5, 0.5),
            self.terminal.screen.width / 2,
            self.terminal.screen.height / 2)
        self.score = 0
        self.score_label = DigitsSheet.get_text_sprites(self.score, 2, 2)
        for i in self.score_label:
            self.add(i)
        self.add(self.gameover)
        self.add(self.character)
        self.add(self.ground_01)
        self.add(self.obstacle)
        self.anim_character()
        self.process()
        self.increase_score()
        self.terminal.bind(' ', self.espace_key_handler)

    def increase_score(self):
        self.timer.after(3, self.increase_score)
        if self.playing:
            self.score += 1
            for i in self.score_label:
                self.remove(i)
            self.score_label = DigitsSheet.get_text_sprites(self.score, 2, 2)
            for i in self.score_label:
                self.add(i)

    def process(self):
        self.timer.after(1, self.process)

        if self.playing:
            self.obstacle.x -= 2
            if (self.obstacle.x + self.obstacle.size[0]) <= 0:
                self.obstacle.x = self.terminal.screen.width

            if self.character.is_touching(self.obstacle):
                self.playing = False
                self.gameover.visible = True
            else:
                if self.character_state == GameScene.JUMP_UP:
                    self.character.y -= 2
                    if self.character.y <= self.terminal.screen.height - 20:
                        self.character_state = GameScene.JUMP_DOWN

                if self.character_state == GameScene.JUMP_DOWN:
                    self.character.y += 2
                    if self.character.y >= self.terminal.screen.height - 7:
                        self.character.y = self.terminal.screen.height - 7
                        self.character_state = GameScene.WALKING

    def espace_key_handler(self):
        if not self.playing:
            self.playing = True
            self.gameover.visible = False
            self.score = 0
            self.obstacle.x = 70
        else:
            if self.character_state == GameScene.WALKING:
                self.character_state = GameScene.JUMP_UP

    def anim_character(self):
        if self.playing:
            if self.character_state == GameScene.WALKING:
                self.character.next_frame()
            elif self.character_state == GameScene.JUMP_UP:
                self.character.frame_index = 3
            elif self.character_state == GameScene.JUMP_DOWN:
                self.character.frame_index = 0
        self.timer.after(3, self.anim_character)


class JumperApp(terminal.CalciumTerminal):
    def __init__(self, *args, **kwargs):
        terminal.CalciumTerminal.__init__(self, *args, **kwargs)
        self.bind('q', self.quit, '+')
        self.logo_scene = CalciumLogoScene(self)
        self.scene = self.logo_scene
        self.game_scene = GameScene(self)
        self.timer = Timer()
        self.timer.after(50, self.after_logo)

    def after_logo(self):
        self.scene = self.game_scene

    def run(self):
        self.scene.draw()
        self.go_to_0_0()
        self.draw()
        self.timer.process()


if __name__ == '__main__':
    if '--help' in sys.argv:
        print('''Help the main character to jump obstacles.
            Use space key to jump. ESC or 'q' quits''')
        sys.exit(0)
    w, h = GTS()
    JumperApp(w, h * 2).mainloop()
