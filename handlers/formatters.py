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


STATUS_LABELS = {
    STATUS_AWAITING_PAYMENT: "🟡 Ожидает оплаты",
    STATUS_PENDING_REVIEW: "🟠 Проверяем оплату",
    STATUS_COMPLETED: "🟢 Выполнен",
    STATUS_CANCELLED: "🔴 Отменен",
}

PAYMENT_UNAVAILABLE_TEXT = "Реквизиты временно недоступны. Обратитесь в поддержку."


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def product_label(order: Order) -> str:
    if order.product_type == PRODUCT_STARS:
        return "Telegram Stars"
    if order.product_type == PRODUCT_PREMIUM:
        return "Telegram Premium"
    return order.product_type


def product_details(order: Order) -> str:
    if order.product_type == PRODUCT_STARS:
        return f"Количество: {order.stars_amount} Stars"
    if order.product_type == PRODUCT_PREMIUM:
        return f"Срок: {premium_duration_label(order.premium_months)}"
    return "Услуга: неизвестно"


def format_order_summary(
    order: Order,
    sbp_phone: Optional[str] = None,
    sbp_name: Optional[str] = None,
) -> str:
    icon = "⭐" if order.product_type == PRODUCT_STARS else "💎"
    if order.status == STATUS_AWAITING_PAYMENT:
        return (
            f"{icon} Заказ {product_label(order)}\n\n"
            f"{product_details(order)}\n"
            f"Получатель: {order.telegram_username}\n"
            f"Сумма к оплате: {order.price_rub} ₽\n\n"
            f"{format_payment_requisites(sbp_phone, sbp_name)}\n\n"
            "После перевода нажмите:\n"
            "✅ Я оплатил"
        )

    text = (
        f"{icon} Заказ {product_label(order)}\n\n"
        f"Номер: #{order.id}\n"
        f"{product_details(order)}\n"
        f"Получатель: {order.telegram_username}\n"
        f"Сумма к оплате: {order.price_rub} ₽\n\n"
        f"Статус: {status_label(order.status)}"
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


def format_admin_order(order: Order) -> str:
    return (
        "🆕 Новый заказ\n\n"
        f"Номер: #{order.id}\n"
        f"Услуга: {product_label(order)}\n"
        f"{product_details(order)}\n"
        f"Получатель: {order.telegram_username}\n"
        f"Сумма: {order.price_rub} ₽\n"
        f"Клиент ID: {order.user_id}\n\n"
        f"Статус: {status_label(order.status)}"
    )


def format_admin_completion_confirmation(order_id: int) -> str:
    return f"Подтвердить выполнение заказа #{order_id}?"


def format_orders_list(orders: Iterable[Order]) -> str:
    orders = list(orders)
    if not orders:
        return "У вас пока нет заказов."

    lines = ["📦 Мои заказы"]
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
            f"Telegram Premium на {premium_duration_label(order.premium_months)} "
            f"оформлен для {order.telegram_username}.\n"
            "Спасибо за покупку в StarDrop."
        )
    return (
        "✅ Заказ выполнен\n\n"
        f"{order.stars_amount} Stars отправлены на {order.telegram_username}.\n"
        "Спасибо за покупку в StarDrop."
    )
