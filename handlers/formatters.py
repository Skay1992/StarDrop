from typing import Iterable, Optional

from config.pricing import premium_duration_label
from database.orders import (
    Order,
    PRODUCT_PREMIUM,
    PRODUCT_STARS,
    STATUS_AWAITING_PAYMENT,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_PENDING_REVIEW,
)
from database.support import STATUS_ANSWERED, STATUS_CLOSED, STATUS_OPEN


STATUS_LABELS = {
    STATUS_AWAITING_PAYMENT: "🟡 Ожидает оплаты",
    STATUS_PENDING_REVIEW: "🟠 Проверяем оплату",
    STATUS_COMPLETED: "🟢 Выполнен",
    STATUS_CANCELLED: "🔴 Отменен",
}
SUPPORT_STATUS_LABELS = {
    STATUS_OPEN: "🟠 Открыто",
    STATUS_ANSWERED: "🟢 Ответ получен",
    STATUS_CLOSED: "⚫ Закрыто",
}

PAYMENT_UNAVAILABLE_TEXT = "Реквизиты временно недоступны. Обратитесь в поддержку."


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, "⚪ Неизвестен")


def support_status_label(status: str) -> str:
    return SUPPORT_STATUS_LABELS.get(status, "⚪ Неизвестно")


def product_label(order: Order) -> str:
    if order.product_type == PRODUCT_STARS:
        return "Telegram Stars"
    if order.product_type == PRODUCT_PREMIUM:
        return "Telegram Premium"
    return order.product_type


def product_details(order: Order) -> str:
    if order.product_type == PRODUCT_STARS:
        return f"Количество: {order.stars_amount} звезд"
    if order.product_type == PRODUCT_PREMIUM:
        return f"Срок: {premium_duration_label(order.premium_months)}"
    return "Услуга: неизвестно"


def format_order_summary(
    order: Order,
    sbp_phone: Optional[str] = None,
    sbp_name: Optional[str] = None,
) -> str:
    icon = "⭐" if order.product_type == PRODUCT_STARS else "💎"
    if order.product_type == PRODUCT_STARS:
        quantity = f"Количество:\n{order.stars_amount} ⭐"
    else:
        quantity = f"Срок:\n{order.premium_months} мес."

    text = (
        f"📦 Заказ №{order.id}\n\n"
        f"{icon} {product_label(order)}\n\n"
        f"{quantity}\n\n"
        "👤 Получатель:\n"
        f"{order.telegram_username}\n\n"
        "💰 К оплате:\n"
        f"{order.price_rub} ₽\n\n"
        "Статус:\n"
        f"{status_label(order.status)}"
    )

    if order.status == STATUS_AWAITING_PAYMENT:
        text += (
            f"\n\n{format_payment_requisites(sbp_phone, sbp_name)}\n\n"
            "После оплаты нажмите:\n"
            "✅ Я оплатил"
        )

    return text


def format_payment_requisites(sbp_phone: Optional[str], sbp_name: Optional[str]) -> str:
    if not sbp_phone or not sbp_name:
        return PAYMENT_UNAVAILABLE_TEXT

    return (
        "Реквизиты для оплаты:\n\n"
        "СБП:\n"
        f"{sbp_phone}\n\n"
        "Получатель:\n"
        f"{sbp_name}"
    )


def format_payment_review_message(order: Order) -> str:
    return (
        "✅ Спасибо!\n\n"
        f"Заказ №{order.id} отправлен на проверку.\n"
        "Мы уведомим вас после выполнения."
    )


def format_cancelled_message() -> str:
    return (
        "❌ Заказ отменен\n\n"
        "Если вы оплатили заказ случайно, напишите в поддержку."
    )


def format_admin_order(order: Order) -> str:
    icon = "⭐" if order.product_type == PRODUCT_STARS else "💎"
    if order.product_type == PRODUCT_STARS:
        quantity = f"Количество:\n{order.stars_amount} ⭐"
    else:
        quantity = f"Срок:\n{order.premium_months} мес."

    return (
        f"🆕 Заказ №{order.id}\n\n"
        "Услуга:\n"
        f"{icon} {product_label(order)}\n\n"
        f"{quantity}\n\n"
        "👤 Получатель:\n"
        f"{order.telegram_username}\n\n"
        "💰 Сумма:\n"
        f"{order.price_rub} ₽\n\n"
        "👤 Клиент:\n"
        f"{order.user_id}\n\n"
        "Статус:\n"
        f"{status_label(order.status)}"
    )


def format_admin_completion_confirmation(order_id: int) -> str:
    return f"Подтвердить выполнение заказа №{order_id}?"


def format_orders_list(orders: Iterable[Order]) -> str:
    orders = list(orders)
    if not orders:
        return "📦 Мои заказы\n\nУ вас пока нет заказов."

    lines = ["📦 Последние заказы"]
    for order in orders:
        if order.product_type == PRODUCT_STARS:
            service = f"⭐ {order.stars_amount} звезд"
        else:
            service = f"💎 Telegram Premium, {order.premium_months} мес."
        lines.extend(
            [
                "",
                f"#{order.id} — {service} — {order.price_rub} ₽",
                f"Статус: {status_label(order.status)}",
                f"Получатель: {order.telegram_username}",
            ]
        )
    return "\n".join(lines)


def format_admin_orders_list(orders: Iterable[Order], title: str) -> str:
    orders = list(orders)
    if not orders:
        return f"{title}\n\nЗаказов нет."

    lines = [title]
    for order in orders:
        lines.extend(
            [
                "",
                f"#{order.id} · {product_label(order)}",
                product_details(order),
                f"Получатель: {order.telegram_username}",
                f"Сумма: {order.price_rub} ₽",
                f"Статус: {status_label(order.status)}",
                f"Дата: {order.created_at}",
            ]
        )
    return "\n".join(lines)


def format_completed_message(order: Order) -> str:
    if order.product_type == PRODUCT_PREMIUM:
        return (
            "✅ Заказ выполнен\n\n"
            f"Telegram Premium на {order.premium_months} мес. "
            f"оформлен для {order.telegram_username}.\n\n"
            "Спасибо за покупку в StarDrop!"
        )
    return (
        "✅ Заказ выполнен\n\n"
        f"{order.stars_amount} ⭐ отправлены на {order.telegram_username}.\n\n"
        "Спасибо за покупку в StarDrop!"
    )
