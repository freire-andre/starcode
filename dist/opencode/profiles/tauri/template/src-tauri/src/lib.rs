#[tauri::command]
fn greet(name: &str) -> String {
    let who = name.trim();
    if who.is_empty() {
        "Olá, mundo!".to_string()
    } else {
        format!("Olá, {who}!")
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("erro ao executar a aplicação Tauri");
}

#[cfg(test)]
mod tests {
    use super::greet;

    #[test]
    fn greets_by_name() {
        assert_eq!(greet(" Ana "), "Olá, Ana!");
    }

    #[test]
    fn greets_the_world_when_empty() {
        assert_eq!(greet("  "), "Olá, mundo!");
    }
}
