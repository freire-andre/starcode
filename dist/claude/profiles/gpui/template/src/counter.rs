//! Lógica do contador, sem dependência da interface.

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct Counter {
    value: i64,
}

impl Counter {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn value(&self) -> i64 {
        self.value
    }

    pub fn increment(&mut self) {
        self.value = self.value.saturating_add(1);
    }

    pub fn decrement(&mut self) {
        self.value = self.value.saturating_sub(1);
    }

    pub fn reset(&mut self) {
        self.value = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn starts_at_zero() {
        assert_eq!(Counter::new().value(), 0);
    }

    #[test]
    fn increment_and_decrement_change_value() {
        let mut counter = Counter::new();
        counter.increment();
        counter.increment();
        counter.decrement();
        assert_eq!(counter.value(), 1);
    }

    #[test]
    fn reset_returns_to_zero() {
        let mut counter = Counter::new();
        counter.increment();
        counter.reset();
        assert_eq!(counter.value(), 0);
    }

    #[test]
    fn saturates_instead_of_overflowing() {
        let mut counter = Counter { value: i64::MAX };
        counter.increment();
        assert_eq!(counter.value(), i64::MAX);
    }
}
