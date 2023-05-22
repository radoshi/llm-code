from llm_code.db import Database, DBModel, get_last_inserted_row


def test_create_database(tmpdir):
    db_path = tmpdir / "db.sqlite"
    assert not db_path.exists()
    db = Database.get(db_path)
    assert db.url.drivername == "sqlite"
    assert db.url.database == str(db_path)


def test_get_last_inserted_row(tmpdir):
    db_path = tmpdir / "db.sqlite"
    _ = Database.get(db_path)

    db_entry = DBModel(
        model="test_model",
        temperature=1.0,
        max_tokens=1,
        system_message="test_system_message",
        user_message="test_user_message",
        assistant_message="test_assistant_message",
        input_tokens=1,
        output_tokens=1,
    )
    with Database.session() as s:
        s.add(db_entry)
        s.commit()

    result = get_last_inserted_row()
    assert isinstance(result, DBModel)
    assert result.model == "test_model"
    assert result.temperature == 1.0
    assert result.max_tokens == 1
    assert result.system_message == "test_system_message"
    assert result.user_message == "test_user_message"
    assert result.assistant_message == "test_assistant_message"
    assert result.input_tokens == 1
    assert result.output_tokens == 1
    assert result.temperature == 1.0
    assert result.max_tokens == 1
    assert result.system_message == "test_system_message"
    assert result.user_message == "test_user_message"
    assert result.assistant_message == "test_assistant_message"
    assert result.input_tokens == 1
    assert result.output_tokens == 1
