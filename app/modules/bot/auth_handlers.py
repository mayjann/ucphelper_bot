from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command


class AuthStates(StatesGroup):
    login = State()
    password = State()
    code = State()


auth = {
    "login": None,
    "password": None,
    "awaiting": False
}


def create_auth_router(auth_browser, user_id: int):
    router = Router()

    @router.message(AuthStates.login, F.from_user.id == user_id)
    async def step_login(msg: Message, state: FSMContext):
        await state.update_data(login=msg.text)
        await state.set_state(AuthStates.password)
        await msg.answer("Password:")

    @router.message(AuthStates.password, F.from_user.id == user_id)
    async def step_password(msg: Message, state: FSMContext):
        data = await state.get_data()

        auth["login"] = data["login"]
        auth["password"] = msg.text

        await auth_browser.start_login(data["login"], msg.text)

        await state.update_data(password=msg.text)
        await state.set_state(AuthStates.code)

        await msg.answer("Code:")

    @router.message(AuthStates.code, F.from_user.id == user_id)
    async def step_code(msg: Message, state: FSMContext):
        await auth_browser.submit_code(msg.text)

        await state.clear()
        auth["awaiting"] = False

        await msg.answer("Авторизация выполнена")

    return router