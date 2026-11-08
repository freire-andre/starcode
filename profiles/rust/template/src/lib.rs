//! Biblioteca do projeto.

/// Monta a saudação usada pelo binário.
pub fn greeting(name: &str) -> String {
    format!("Olá, {name}!")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn greeting_includes_name() {
        assert_eq!(greeting("mundo"), "Olá, mundo!");
    }
}
