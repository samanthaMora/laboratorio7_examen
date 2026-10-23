import book
import user
import library
import pytest

@pytest.mark.unit
def test_borrow_book():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    assert book1.title == 'El Alquimista'
    book1.borrow()
    assert book1.borrowed == True

@pytest.mark.unit
def test_re_borrow_book():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    assert book1.title == 'El Alquimista'
    book1.borrow()
    assert book1.borrowed == True
    with pytest.raises(ValueError, match="The book is already borrowed"):
        book1.borrow()

@pytest.mark.unit
def test_borrow_and_return_book():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    assert book1.title == 'El Alquimista'
    book1.borrow()
    assert book1.borrowed == True
    book1.return_book()
    assert book1.borrowed == False

@pytest.mark.system
def test_library_borrow():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    miguel = user.User('Miguel', 'ID0001')
    lib = library.Library()
    lib.add_book(book1)
    assert lib.books[0].title == 'El Alquimista'
    lib.add_user(miguel)
    #corroborar que se agregó
    assert lib.users[0].name == 'Miguel'
    lib.borrow_book('ID0001','ISBN0001')
    assert book1.borrowed == True

@pytest.fixture
def library_init():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    miguel = user.User('Miguel', 'ID0001')
    lib = library.Library()
    lib.add_book(book1)
    lib.add_user(miguel)
    return lib

@pytest.mark.wip
def test_library_borrow_fixture(library_init):
    lib = library_init
    #corroborar que se agregó
    assert lib.users[0].name == 'Miguel'
    lib.borrow_book('ID0001','ISBN0001')
    assert lib.books[0].borrowed == True

# ---------------------------------------------------------------------
# Pruebas adicionales 
# Temas: parametrize, monkeypatch.setitem, capsys, monkeypatch.delattr,
#        try-except, cobertura de caja blanca (+ fixture, marcadores,
#        pytest.raises y pytest.ini)
# ---------------------------------------------------------------------


# 1. Parametrize + pytest.raises + fixture: misma prueba, varios datos
@pytest.mark.unit
@pytest.mark.parametrize("user_id, isbn, mensaje", [
    ('ID9999', 'ISBN0001', 'User not found'),
    ('ID0001', 'ISBN9999', 'Book not found'),
    ('', '', 'User not found'),
])
def test_borrow_invalid_data(library_init, user_id, isbn, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        library_init.borrow_book(user_id, isbn)


# 2. monkeypatch.setitem + capsys: cambiar un diccionario global y capturar print()
@pytest.mark.unit
def test_loans_disabled(library_init, monkeypatch, capsys):
    monkeypatch.setitem(library.settings, "loans_enabled", False)
    library_init.borrow_book('ID0001', 'ISBN0001')
    salida = capsys.readouterr().out
    assert "Loans are disabled" in salida
    assert library_init.books[0].borrowed == False


# 3. monkeypatch.delattr: eliminar temporalmente un método y verificar que falla
@pytest.mark.unit
def test_borrow_without_register_method(library_init, monkeypatch):
    monkeypatch.delattr(user.User, "register_borrow")
    with pytest.raises(AttributeError):
        library_init.borrow_book('ID0001', 'ISBN0001')


# 4. try-except: verificar una excepción sin usar pytest.raises
@pytest.mark.unit
def test_return_not_borrowed_try_except():
    book1 = book.Book('El Alquimista', 'Paulo Coehlo', 1967, 'ISBN0001')
    try:
        book1.return_book()
        pytest.fail("Se esperaba ValueError y no se lanzó")
    except ValueError as e:
        assert str(e) == "The book is not currently borrowed"
    assert book1.borrowed == False


# 5. Cobertura de caja blanca: recorrer TODAS las ramas de Library.borrow_book
#    (loans deshabilitado / usuario inexistente / libro inexistente / éxito)
#    Ejecutar con: pytest --cov=. --cov-branch --cov-report=term-missing
@pytest.mark.integration
def test_borrow_book_all_branches(library_init, monkeypatch, capsys):
    # Rama 1: préstamos deshabilitados
    monkeypatch.setitem(library.settings, "loans_enabled", False)
    library_init.borrow_book('ID0001', 'ISBN0001')
    assert "Loans are disabled" in capsys.readouterr().out
    monkeypatch.setitem(library.settings, "loans_enabled", True)
    # Rama 2: usuario no encontrado
    with pytest.raises(ValueError, match="User not found"):
        library_init.borrow_book('ID9999', 'ISBN0001')
    # Rama 3: libro no encontrado
    with pytest.raises(ValueError, match="Book not found"):
        library_init.borrow_book('ID0001', 'ISBN9999')
    # Rama 4: camino feliz (préstamo exitoso, se registra en el historial)
    library_init.borrow_book('ID0001', 'ISBN0001')
    assert library_init.books[0].borrowed == True
    assert len(library_init.users[0].get_history()) == 1
