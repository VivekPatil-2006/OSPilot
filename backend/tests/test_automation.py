import os
import pytest
from app.services.desktop_automation_service import desktop_automation


@pytest.fixture
def temp_workspace(tmp_path):
    d = tmp_path / "test_automation_space"
    d.mkdir()
    return str(d)


def test_create_folder(temp_workspace):
    new_dir = os.path.join(temp_workspace, "sub_folder")
    res = desktop_automation.create_folder(new_dir)
    assert res["status"] == "success"
    assert os.path.exists(new_dir)


def test_rename_and_move_file(temp_workspace):
    # Create initial file
    src_file = os.path.join(temp_workspace, "initial.txt")
    with open(src_file, "w", encoding="utf-8") as f:
        f.write("Test content")

    # Test Rename
    res_rename = desktop_automation.rename_file(src_file, "renamed.txt")
    assert res_rename["status"] == "success"
    renamed_path = res_rename["new_path"]
    assert os.path.exists(renamed_path)
    assert not os.path.exists(src_file)

    # Test Move
    dest_dir = os.path.join(temp_workspace, "dest_dir")
    os.makedirs(dest_dir, exist_ok=True)
    res_move = desktop_automation.move_file(renamed_path, os.path.join(dest_dir, "renamed.txt"))
    assert res_move["status"] == "success"
    moved_path = res_move["destination_path"]
    assert os.path.exists(moved_path)
    assert not os.path.exists(renamed_path)


def test_delete_file_confirmation_guardrail(temp_workspace):
    target_file = os.path.join(temp_workspace, "to_delete.txt")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("Delete me")

    # Unconfirmed delete MUST require confirmation and NOT delete
    res_unconfirmed = desktop_automation.delete_file(target_file, confirmed=False)
    assert res_unconfirmed["status"] == "confirmation_required"
    assert res_unconfirmed["requires_confirmation"] is True
    assert os.path.exists(target_file)

    # Confirmed delete MUST succeed
    res_confirmed = desktop_automation.delete_file(target_file, confirmed=True)
    assert res_confirmed["status"] == "success"
    assert not os.path.exists(target_file)


def test_app_close_confirmation_guardrail():
    res_unconfirmed = desktop_automation.close_application("notepad.exe", confirmed=False)
    assert res_unconfirmed["status"] == "confirmation_required"
    assert res_unconfirmed["requires_confirmation"] is True
    assert "notepad.exe" in res_unconfirmed["warning"]


def test_open_browser():
    res = desktop_automation.open_browser("example.com")
    assert res["status"] == "success"
    assert res["url"] == "https://example.com"


def test_take_screenshot(temp_workspace):
    res = desktop_automation.take_screenshot(save_dir=temp_workspace)
    assert res["status"] == "success"
    assert os.path.exists(res["file_path"])
    assert res["width"] > 0
    assert res["height"] > 0


def test_volume_control():
    res_mute = desktop_automation.control_volume("mute")
    assert res_mute["status"] == "success"

    res_set = desktop_automation.control_volume("set", level=50)
    assert res_set["status"] == "success"


def test_clipboard_operations():
    test_text = "OSPilot Automation Test Clipboard"
    res_set = desktop_automation.set_clipboard(test_text)
    assert res_set["status"] == "success"

    res_get = desktop_automation.get_clipboard()
    assert res_get["status"] == "success"
    assert res_get["text"] == test_text


def test_power_state_confirmation_guardrail():
    # Shutdown unconfirmed
    res_sd = desktop_automation.shutdown_system(confirmed=False)
    assert res_sd["status"] == "confirmation_required"
    assert res_sd["requires_confirmation"] is True

    # Restart unconfirmed
    res_rs = desktop_automation.restart_system(confirmed=False)
    assert res_rs["status"] == "confirmation_required"
    assert res_rs["requires_confirmation"] is True

    # Sleep unconfirmed
    res_sl = desktop_automation.sleep_system(confirmed=False)
    assert res_sl["status"] == "confirmation_required"
    assert res_sl["requires_confirmation"] is True


from unittest.mock import patch

def test_execute_voice_command():
    # Test volume voice command
    res_vol = desktop_automation.execute_voice_command("Set Laptop Volume to 45")
    assert res_vol["status"] == "success"
    assert res_vol["action"] == "control_volume"
    assert "45%" in res_vol["response_text"]

    # Test open application voice command with mock to prevent physical app launch
    with patch.object(desktop_automation, 'open_application', return_value={"status": "success", "application": "Google Chrome"}):
        res_app = desktop_automation.execute_voice_command("Open Google Chrome")
        assert res_app["status"] == "success"
        assert res_app["action"] == "open_application"

    # Test dangerous delete file voice command
    res_del = desktop_automation.execute_voice_command("Delete file temp.txt")
    assert res_del["status"] == "confirmation_required"
    assert res_del["requires_confirmation"] is True

    # Test camera photo voice command with mock to prevent opening camera GUI app during test runs
    with patch.object(desktop_automation, 'capture_camera_photo', return_value={"status": "success", "file_path": "mock_photo.png"}):
        res_cam = desktop_automation.execute_voice_command("open camera and click picture")
        assert res_cam["status"] == "success"
        assert "Photo captured" in res_cam["response_text"] or "Camera photo" in res_cam["response_text"]

    # Test edge search voice command with mock to prevent opening browser windows
    with patch.object(desktop_automation, 'open_browser', return_value={"status": "success", "url": "https://www.bing.com/search?q=news"}):
        res_edge = desktop_automation.execute_voice_command("Open Microsoft edge and search for news")
        assert res_edge["status"] == "success"
        assert res_edge["action"] == "open_browser"
        assert "Microsoft Edge" in res_edge["response_text"]
        assert "news" in res_edge["response_text"]

    # Test IP address query command
    res_ip = desktop_automation.execute_voice_command("What is my IP address")
    assert res_ip["status"] == "success"
    assert res_ip["action"] == "system_info"
    assert "IP Address" in res_ip["response_text"]

    # Test Special Folder command with mock to prevent launching Explorer
    with patch.object(desktop_automation, 'open_special_folder', return_value={"status": "success", "folder_path": "C:\\Users\\Mock\\Downloads"}):
        res_folder = desktop_automation.execute_voice_command("Open Downloads folder")
        assert res_folder["status"] == "success"
        assert res_folder["action"] == "open_folder"

    # Test YouTube Search command with mock to prevent opening browser windows
    with patch.object(desktop_automation, 'open_browser', return_value={"status": "success", "url": "https://www.youtube.com"}):
        res_yt = desktop_automation.execute_voice_command("Search YouTube for lofi music")
        assert res_yt["status"] == "success"
        assert res_yt["action"] == "open_browser"
        assert "YouTube" in res_yt["response_text"]

    # Test brightness voice command
    with patch.object(desktop_automation, 'control_brightness', return_value={"status": "success", "brightness": 100}):
        res_b = desktop_automation.execute_voice_command("Set brightness to 100")
        assert res_b["status"] == "success"
        assert res_b["action"] == "control_brightness"
        assert "100%" in res_b["response_text"]

    # Test Telegram / WhatsApp message voice command with mock to prevent physical GUI typing during unit tests
    with patch.object(desktop_automation, 'send_desktop_chat_message', return_value={"status": "success", "platform": "telegram", "recipient": "Raj", "message": "Hi"}):
        res_msg = desktop_automation.execute_voice_command("open telegram and send Hi message to Raj")
        assert res_msg["status"] == "success"
        assert res_msg["action"] == "send_chat_message"
        assert "Telegram" in res_msg["response_text"]
        assert "Raj" in res_text if 'res_text' in locals() else "Raj" in res_msg["response_text"]

