mod counter;

use counter::Counter;
use gpui::{
    div, prelude::*, px, rgb, size, App, Application, Bounds, Context, Window, WindowBounds,
    WindowOptions,
};

struct CounterView {
    counter: Counter,
}

impl CounterView {
    fn button(
        label: &'static str,
        id: &'static str,
        cx: &mut Context<Self>,
        action: fn(&mut Counter),
    ) -> impl IntoElement {
        div()
            .id(id)
            .px_4()
            .py_2()
            .rounded_md()
            .bg(rgb(0x3b82f6))
            .cursor_pointer()
            .child(label)
            .on_click(cx.listener(move |this, _event, _window, cx| {
                action(&mut this.counter);
                cx.notify();
            }))
    }
}

impl Render for CounterView {
    fn render(&mut self, _window: &mut Window, cx: &mut Context<Self>) -> impl IntoElement {
        div()
            .flex()
            .flex_col()
            .gap_4()
            .size_full()
            .justify_center()
            .items_center()
            .bg(rgb(0x1e1e2e))
            .text_color(rgb(0xffffff))
            .child(div().text_xl().child(format!("{}", self.counter.value())))
            .child(
                div()
                    .flex()
                    .gap_2()
                    .child(Self::button("-", "decrement", cx, Counter::decrement))
                    .child(Self::button("+", "increment", cx, Counter::increment))
                    .child(Self::button("0", "reset", cx, Counter::reset)),
            )
    }
}

fn main() {
    Application::new().run(|cx: &mut App| {
        let bounds = Bounds::centered(None, size(px(320.), px(240.)), cx);
        cx.open_window(
            WindowOptions {
                window_bounds: Some(WindowBounds::Windowed(bounds)),
                ..Default::default()
            },
            |_, cx| {
                cx.new(|_| CounterView {
                    counter: Counter::new(),
                })
            },
        )
        .expect("falha ao abrir a janela");
        cx.activate(true);
    });
}
