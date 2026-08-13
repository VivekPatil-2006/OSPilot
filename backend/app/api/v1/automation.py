from fastapi import APIRouter, HTTPException, status
from app.domain.schemas import (
    AppOpenRequest, AppCloseRequest,
    CreateFolderRequest, RenameFileRequest, MoveFileRequest, DeleteFileRequest,
    OpenBrowserRequest, VolumeControlRequest, ClipboardSetRequest, PowerStateRequest,
    AutomationActionResult, VoiceCommandRequest, VoiceAudioRequest, VoiceCommandResponse
)
from app.services.desktop_automation_service import desktop_automation

router = APIRouter(prefix="/automation", tags=["Desktop Automation"])


@router.post("/voice-command", response_model=VoiceCommandResponse)
def execute_voice_command(req: VoiceCommandRequest) -> VoiceCommandResponse:
    """Parses and executes spoken voice instructions for desktop control."""
    try:
        res = desktop_automation.execute_voice_command(req.command)
        return VoiceCommandResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/voice-audio", response_model=VoiceCommandResponse)
def execute_voice_audio(req: VoiceAudioRequest) -> VoiceCommandResponse:
    """Transcribes microphone WAV audio into text and executes desktop command."""
    try:
        res = desktop_automation.execute_voice_audio_command(req.audio_base64)
        return VoiceCommandResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Application Management ---

@router.post("/app/open", response_model=AutomationActionResult)
def open_application(req: AppOpenRequest) -> AutomationActionResult:
    """Launches an application by executable name or path."""
    try:
        res = desktop_automation.open_application(req.app_name_or_path)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/app/close", response_model=AutomationActionResult)
def close_application(req: AppCloseRequest) -> AutomationActionResult:
    """Closes an application. Dangerous action requiring confirmation & password."""
    try:
        res = desktop_automation.close_application(req.app_name, confirmed=req.confirmed, password=req.password)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            requires_confirmation=res.get("requires_confirmation"),
            warning=res.get("warning"),
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- File Operations ---

@router.post("/file/create-folder", response_model=AutomationActionResult)
def create_folder(req: CreateFolderRequest) -> AutomationActionResult:
    """Creates a directory tree at target path or location + folder_name."""
    try:
        res = desktop_automation.create_folder(
            folder_path=req.folder_path,
            parent_path=req.parent_path,
            folder_name=req.folder_name
        )
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/file/rename", response_model=AutomationActionResult)
def rename_file(req: RenameFileRequest) -> AutomationActionResult:
    """Renames a file or folder."""
    try:
        res = desktop_automation.rename_file(req.source_path, req.new_name_or_path)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/file/move", response_model=AutomationActionResult)
def move_file(req: MoveFileRequest) -> AutomationActionResult:
    """Moves a file or folder to a target destination."""
    try:
        res = desktop_automation.move_file(req.source_path, req.destination_path)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/file/delete", response_model=AutomationActionResult)
def delete_file(req: DeleteFileRequest) -> AutomationActionResult:
    """Deletes a file or directory. Dangerous action requiring explicit confirmation & password."""
    try:
        res = desktop_automation.delete_file(req.file_path, confirmed=req.confirmed, password=req.password)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            requires_confirmation=res.get("requires_confirmation"),
            warning=res.get("warning"),
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Browser & Display ---

@router.post("/browser/open", response_model=AutomationActionResult)
def open_browser(req: OpenBrowserRequest) -> AutomationActionResult:
    """Opens default web browser to the target URL."""
    try:
        res = desktop_automation.open_browser(req.url)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/screenshot", response_model=AutomationActionResult)
def take_screenshot() -> AutomationActionResult:
    """Captures the current screen and saves an image artifact."""
    try:
        res = desktop_automation.take_screenshot()
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Hardware & Clipboard Controls ---

@router.post("/volume", response_model=AutomationActionResult)
def control_volume(req: VolumeControlRequest) -> AutomationActionResult:
    """Controls system volume (mute, unmute, set level, volume up/down)."""
    try:
        res = desktop_automation.control_volume(req.action, req.level)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clipboard", response_model=AutomationActionResult)
def get_clipboard() -> AutomationActionResult:
    """Reads system clipboard text."""
    try:
        res = desktop_automation.get_clipboard()
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clipboard", response_model=AutomationActionResult)
def set_clipboard(req: ClipboardSetRequest) -> AutomationActionResult:
    """Writes text into system clipboard."""
    try:
        res = desktop_automation.set_clipboard(req.text)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- System Power Management ---

@router.post("/power/shutdown", response_model=AutomationActionResult)
def shutdown_system(req: PowerStateRequest) -> AutomationActionResult:
    """Initiates system shutdown. Dangerous action requiring confirmation & password."""
    try:
        res = desktop_automation.shutdown_system(confirmed=req.confirmed, delay_seconds=req.delay_seconds, password=req.password)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            requires_confirmation=res.get("requires_confirmation"),
            warning=res.get("warning"),
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/power/restart", response_model=AutomationActionResult)
def restart_system(req: PowerStateRequest) -> AutomationActionResult:
    """Initiates system restart. Dangerous action requiring confirmation & password."""
    try:
        res = desktop_automation.restart_system(confirmed=req.confirmed, delay_seconds=req.delay_seconds, password=req.password)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            requires_confirmation=res.get("requires_confirmation"),
            warning=res.get("warning"),
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/power/sleep", response_model=AutomationActionResult)
def sleep_system(req: PowerStateRequest) -> AutomationActionResult:
    """Initiates system sleep mode. Dangerous action requiring confirmation & password."""
    try:
        res = desktop_automation.sleep_system(confirmed=req.confirmed, password=req.password)
        return AutomationActionResult(
            status=res["status"],
            action=res["action"],
            requires_confirmation=res.get("requires_confirmation"),
            warning=res.get("warning"),
            details=res
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
