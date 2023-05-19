import pytest

from llm_code.templates import Message, Template, TemplateLibrary


def write_toml_file(path):
    with open(path / "toml_greeting.toml", "w") as f:
        f.write(
            """
            content = "Hello, World!"
            name = "toml_greeting"
            role = "system"
            """
        )
    return Template(content="Hello, World!", name="toml_greeting", role="system")


# Test function for the `message` method
def test_message():
    template = Template(content="Hello, World!", name="greeting", role="system")
    expected_message = {"content": "Hello, World!", "role": "system"}
    assert template.message() == expected_message


# Test function for the `message` method
def test_message_with_kwargs():
    template = Template(content="{hello}, {world}!", name="greeting", role="system")
    expected_message = {"content": "Hello, World!", "role": "system"}
    assert template.message(hello="Hello", world="World") == expected_message


# Test function for the `save` method when a filename is provided
def test_save_with_filename(tmp_path):
    template = Template(content="Hello, World!", name="greeting", role="system")
    filename = tmp_path / "greeting.json"
    template.save(filename)
    assert filename.exists()
    with open(filename) as f:
        assert f.read() == template.json()


# Test function for the `save` method when a filename is not provided but
# the name attribute is set
def test_save_without_filename(tmp_path):
    template = Template(content="Hello, World!", name="greeting", role="system")
    filename = tmp_path / "greeting.json"
    template.save(filename=filename)
    assert filename.exists()
    with open(filename) as f:
        assert f.read() == template.json()


# Test function for the `save` method when neither filename nor name attribute is
# provided
def test_save_without_filename_and_name():
    template = Template(content="Hello, World!", role="system")
    with pytest.raises(ValueError, match="Name must be provided to save the template."):
        template.save()


# Test function for the `save` method when an empty name attribute is provided
def test_save_with_empty_name():
    template = Template(content="Hello, World!", name="", role="system")
    with pytest.raises(ValueError, match="Name must be provided to save the template."):
        template.save()
        template.save()


# Unit test for extract_format_inputs
def test_inputs():
    # Test case 1: Format string with two field names
    template = Template(content="{hello} {world}")
    inputs1 = template.inputs()
    assert inputs1 == ["hello", "world"]

    # Test case 2: Format string with no field names
    template = Template(content="Hello, World!")
    inputs2 = template.inputs()
    assert inputs2 == []

    # Test case 4: Format string with repeated field names
    template = Template(content="{greeting}, {name}. My name is also {name}.")
    inputs3 = template.inputs()
    assert inputs3 == ["greeting", "name"]


# Test function for the `parse_toml` method
def test_parse_toml(tmp_path):
    parsed_template = write_toml_file(tmp_path)
    assert parsed_template == Template(
        name="toml_greeting", content="Hello, World!", role="system"
    )


def test_getitem_setitem():
    library = TemplateLibrary()
    template = Template(content="Hello, World!", name="greeting", role="system")
    library["greeting"] = template  # Calls __setitem__
    assert library["greeting"] == template  # Calls __getitem__


def test_del_item():
    library = TemplateLibrary()
    template = Template(content="Hello, World!", name="greeting", role="system")
    library["greeting"] = template
    del library["greeting"]  # Calls __del_item__
    with pytest.raises(KeyError):
        _ = library["greeting"]


def test_add():
    library = TemplateLibrary()
    template = Template(content="Hello, World!", name="greeting", role="system")
    library.add(template)
    assert library["greeting"] == template


def test_add_without_name():
    library = TemplateLibrary()
    template = Template(content="Hello, World!", role="system")
    with pytest.raises(ValueError, match="Template must have a name."):
        library.add(template)


def test_from_file(tmp_path):
    template = Template(content="Hello, World!", name="greeting", role="system")
    filename = tmp_path / "greeting.json"
    template.save(filename)
    library = TemplateLibrary.from_file_or_directory(filename)
    assert library["greeting"] == template


def test_from_toml_file(tmp_path):
    template = write_toml_file(tmp_path)
    library = TemplateLibrary.from_file_or_directory(tmp_path / "toml_greeting.toml")
    assert library["toml_greeting"] == template


def test_from_directory(tmp_path):
    template1 = Template(content="Hello, World!", name="greeting", role="system")
    template2 = Template(content="Goodbye, World!", name="farewell", role="user")
    filename1 = tmp_path / "greeting.json"
    filename2 = tmp_path / "farewell.json"
    template1.save(filename1)
    template2.save(filename2)
    toml_template = write_toml_file(tmp_path)
    library = TemplateLibrary.from_file_or_directory(tmp_path)
    assert library["greeting"] == template1
    assert library["farewell"] == template2
    assert library["toml_greeting"] == toml_template


def test_from_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        _ = TemplateLibrary.from_file_or_directory("nonexistent.json")


def test_from_nonexistent_directory():
    with pytest.raises(FileNotFoundError):
        _ = TemplateLibrary.from_file_or_directory("nonexistent_dir")
        _ = TemplateLibrary.from_file_or_directory("nonexistent_dir")


def test_message_user_message():
    message = Message.user_message("Hello, world!")
    assert message.role == "user"
    assert message.content == "Hello, world!"


def test_message_system_message():
    message = Message.system_message("Test message")
    assert message.role == "system"
    assert message.content == "Test message"


def test_message_from_message():
    message_dict: dict[str, str] = {"role": "user", "content": "Hello, world!"}
    message = Message.from_message(message_dict)
    assert message.role == "user"
    assert message.content == "Hello, world!"


def test_message_code():
    message = Message.user_message("```python\nprint('Hello, world!')\n```")
    code = message.code()
    assert code is not None
    assert code.code == "print('Hello, world!')"
    assert code.lang == "python"
