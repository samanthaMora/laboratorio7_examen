# Guía para el examen práctico: pytest

Temas de la ruleta, explicados con el código de este laboratorio (sistema de biblioteca).

```bash
pip install pytest pytest-cov
pytest -v                                                  # correr todas las pruebas
pytest -m unit                                             # solo un marcador
pytest --cov=. --cov-branch --cov-report=term-missing      # cobertura
```

---

## 1. Marcadores de pytest

Son **etiquetas** que clasifican las pruebas para correr solo un grupo.

```python
@pytest.mark.unit
def test_borrow_book():
    ...
```

En este proyecto hay 4: `unit`, `system`, `integration` y `wip` (work in progress).

```bash
pytest -m unit                  # solo las unitarias
pytest -m "unit or system"      # unitarias y de sistema
pytest -m "not wip"             # todas menos las que están en progreso
```

**Niveles de prueba:**
- **Unitaria (`unit`)**: prueba **una pieza sola**. Por ejemplo, solo `Book.borrow()`.
- **Integración (`integration`)**: prueba **varias piezas juntas**. Por ejemplo, `Library` + `Book` + `User`.
- **Sistema (`system`)**: prueba **todo el sistema** como lo usaría alguien.

---

## 2. pytest.ini

Es el **archivo de configuración** de pytest:

```ini
[pytest]
log_file = log.log          # guarda los logs en este archivo
log_file_mode = w           # "w" = lo sobrescribe en cada ejecución

markers:                    # aquí se REGISTRAN los marcadores
    wip: work in progress
    system: to test the system
    unit: for unit tests
    integration: integration tests between components
```

**¿Por qué hay que registrar los marcadores?** Si usas `@pytest.mark.algo` sin registrarlo, pytest muestra un **warning** (`PytestUnknownMarkWarning`), porque podría ser un error de dedo.

---

## 3. pytest.raises()

Comprueba que el código **sí lanza un error** cuando debe.

```python
def test_re_borrow_book():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    book1.borrow()
    with pytest.raises(ValueError, match="The book is already borrowed"):
        book1.borrow()      # prestarlo dos veces DEBE fallar
```

- Si dentro del `with` **se lanza** `ValueError`, la prueba **pasa**.
- Si **no se lanza** nada, la prueba **falla**.
- `match=` revisa que el **mensaje** del error contenga ese texto (es una expresión regular).

---

## 4. try-except

Es la forma "manual" de hacer lo mismo que `pytest.raises`, con Python normal:

```python
def test_return_not_borrowed_try_except():
    book1 = book.Book(...)
    try:
        book1.return_book()                     # devolver un libro NO prestado
        pytest.fail("Se esperaba ValueError")   # si llega aquí, no hubo error y falla
    except ValueError as e:
        assert str(e) == "The book is not currently borrowed"
```

**El detalle importante:** sin el `pytest.fail(...)`, si no se lanza el error la prueba **pasaría igual** y no te darías cuenta. Con `pytest.raises` eso no puede pasar, por eso se considera la mejor opción.

| | `pytest.raises` | `try-except` |
|---|---|---|
| Si no hay error | Falla sola | Necesita `pytest.fail()` |
| Código | Más corto | Más largo |
| Uso | Lo recomendado en pytest | Python estándar |

En `main.py`, el **programa** usa `try-except` para que no truene cuando el usuario se equivoca:

```python
try:
    lib.borrow_book(user_id, isbn)
except ValueError as e:
    print("Error:", e)
```

---

## 5. Fixture

Una fixture **prepara datos que varias pruebas reutilizan**, para no repetir el mismo código.

```python
@pytest.fixture
def library_init():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    miguel = user.User('Miguel', 'ID0001')
    lib = library.Library()
    lib.add_book(book1)
    lib.add_user(miguel)
    return lib
```

Para usarla, se **pone su nombre como parámetro** de la prueba y pytest la ejecuta y pasa el resultado:

```python
def test_library_borrow_fixture(library_init):
    library_init.borrow_book('ID0001', 'ISBN0001')
```

- La fixture se ejecuta **de nuevo en cada prueba**, así que cada prueba recibe una biblioteca **nueva y limpia**.
- `monkeypatch` y `capsys` también son **fixtures**, pero ya vienen incluidas en pytest.

---

## 6. Parametrize

Corre **la misma prueba con distintos datos**:

```python
@pytest.mark.parametrize("user_id, isbn, mensaje", [
    ('ID9999', 'ISBN0001', 'User not found'),   # caso 1
    ('ID0001', 'ISBN9999', 'Book not found'),   # caso 2
    ('', '',               'User not found'),   # caso 3
])
def test_borrow_invalid_data(library_init, user_id, isbn, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        library_init.borrow_book(user_id, isbn)
```

- El primer argumento son los **nombres de los parámetros**, en un solo string separado por comas.
- El segundo es una **lista de tuplas**, una por caso.
- pytest lo cuenta como **3 pruebas separadas**:
  ```
  test_borrow_invalid_data[ID9999-ISBN0001-User not found] PASSED
  test_borrow_invalid_data[ID0001-ISBN9999-Book not found] PASSED
  test_borrow_invalid_data[--User not found] PASSED
  ```
- Se puede **combinar con fixtures**: aquí también se usa `library_init`.

---

## 7. capsys

Es una fixture que **captura lo que se imprime con `print()`**:

```python
def test_loans_disabled(library_init, monkeypatch, capsys):
    ...
    library_init.borrow_book('ID0001', 'ISBN0001')   # internamente hace print("Loans are disabled")
    salida = capsys.readouterr().out                 # lee lo impreso
    assert "Loans are disabled" in salida
```

- `capsys.readouterr()` devuelve un objeto con `.out` (salida normal) y `.err` (errores).
- Cada vez que se llama, **vacía** lo capturado.
- **¿Por qué hace falta?** `print()` devuelve `None`, así que la única forma de verificar lo que se imprime es capturarlo.

---

## 8. monkeypatch.setitem

`monkeypatch` sirve para **modificar cosas temporalmente** durante una prueba. Al terminar, **todo se restaura solo**.

`setitem` cambia un **elemento de un diccionario**. En `library.py`:

```python
settings = {"loans_enabled": True}
```

En la prueba:

```python
monkeypatch.setitem(library.settings, "loans_enabled", False)
#                   ^diccionario      ^clave           ^valor nuevo
```

**¿Por qué no hacer simplemente `library.settings["loans_enabled"] = False`?** Porque se **quedaría en False** para todas las pruebas siguientes y las haría fallar. `monkeypatch` lo **deshace automáticamente**.

---

## 9. monkeypatch.delattr

Sirve para **borrar temporalmente un atributo o método** de una clase u objeto:

```python
def test_borrow_without_register_method(library_init, monkeypatch):
    monkeypatch.delattr(user.User, "register_borrow")   # User ya no tiene ese método
    with pytest.raises(AttributeError):
        library_init.borrow_book('ID0001', 'ISBN0001')  # Library intenta llamarlo y truena
```

- Sirve para simular que **algo no existe** y ver cómo reacciona el código.
- El error que se lanza es **`AttributeError`**.
- Al terminar la prueba, el método **vuelve a existir**.

| Método | Qué hace |
|---|---|
| `setattr(obj, "nombre", valor)` | Cambia un atributo o método |
| `delattr(obj, "nombre")` | Borra un atributo o método |
| `setitem(dic, "clave", valor)` | Cambia un elemento de un diccionario |
| `delitem(dic, "clave")` | Borra un elemento de un diccionario |
| `setenv("VAR", "valor")` | Cambia una variable de entorno |

---

## 10. Cobertura de caja blanca

- **Caja negra**: pruebas **sin ver el código**; solo se sabe qué entra y qué debe salir.
- **Caja blanca**: pruebas **viendo el código**, para pasar por **todas las líneas y todas las ramas** (`if`/`else`, `for`, `try`).

```python
def borrow_book(self, user_id, isbn):
    if not settings["loans_enabled"]:   # Rama 1: préstamos deshabilitados
        print("Loans are disabled")
        return
    user = self._find_user(user_id)     # Rama 2: usuario no existe → ValueError
    book = self._find_book(isbn)        # Rama 3: libro no existe → ValueError
    book.borrow()                       # Rama 4: todo bien
    user.register_borrow(book)
```

La prueba `test_borrow_book_all_branches` **pasa por los 4 caminos**.

**Cómo medirla:**

```bash
pytest --cov=. --cov-branch --cov-report=term-missing
```

- `--cov=.`: mide la cobertura de la carpeta actual.
- `--cov-branch`: también mide **ramas**, no solo líneas.
- `--cov-report=term-missing`: muestra **qué líneas faltan**.

```
Name        Stmts  Miss  Branch  BrPart  Cover  Missing
book.py        15     0       4       0   100%
library.py     35     4      10       0    91%   28-32
```

- **Stmts**: líneas de código. **Miss**: líneas que ninguna prueba ejecutó.
- **Branch**: ramas totales. **BrPart**: ramas recorridas solo a medias.
- **Missing 28-32**: es `Library.return_book`, que ninguna prueba llama.

**Ojo:** 100% de cobertura **no significa que no haya bugs**. Solo significa que todo se ejecutó. Por ejemplo, el error de ortografía `"Borrwed"` en `user.py` tiene cobertura y aun así está mal.

---

## Resumen

| Tema | En una frase |
|---|---|
| Marcadores | Etiquetas para clasificar pruebas y filtrarlas con `-m` |
| pytest.ini | Archivo de configuración; ahí se registran los marcadores |
| pytest.raises | Verifica que se lance una excepción |
| try-except | Lo mismo a mano; necesita `pytest.fail()` |
| Fixture | Prepara datos reutilizables; se pasa como parámetro |
| Parametrize | Una prueba con muchos datos de entrada |
| capsys | Captura lo que imprime `print()` |
| monkeypatch.setitem | Cambia temporalmente un valor de un diccionario |
| monkeypatch.delattr | Borra temporalmente un atributo o método |
| Caja blanca | Probar viendo el código para cubrir todas las ramas |
