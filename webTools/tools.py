
import asyncio, json, re, logging


class internalTools():
    def __init__(self, presetsJsonPath) -> None:
        self.presetsJsonPath = presetsJsonPath

    def pharsePrompt(self, topic: str, cards: str, preset: str = "defaultv2"):
        with open(self.presetsJsonPath) as f:
            presets = json.load(f)
        
        for preset in presets:
            if presets[preset]["title"].lower() == preset:
                fixedPrompt = presets[preset]["content"].replace("{COUNT}", str(cards)).replace("{TOPIC}", topic)
                return fixedPrompt
            else: continue
        else:
            return False
        

    def parseGeneratedResponse(self, response_text: str):
        try:
            # remove <think>...</think> blocks and content inside
            response_text = re.sub(r"<think>[\s\S]*?</think>", "", response_text)

            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # if full parse fails, try extracting a fenced JSON block
                match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response_text, re.DOTALL)
                if match:
                    json_str = match.group(1)

                    # remove trailing commas before } or ]
                    json_str = re.sub(r",\s*(\]|\})", r"\1", json_str)

                    return json.loads(json_str)

            print("[ERROR] No JSON found in response.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {e}")
        return False
    

    async def check_docker_container(self):
        """Check if service is running as a Docker container"""
        try:
            # check if we're running inside a container
            try:
                with open('/.dockerenv', 'r'):
                    logging.info("Detected running inside Docker container")
                    return True
            except FileNotFoundError:
                return False
        except Exception as e:
            logging.error(f"Docker check failed: {str(e)}")
            return False

    async def restart_docker_container(self, service_name):
        """Restart Docker container"""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "restart", service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0, stdout.decode(), stderr.decode()
        except Exception as e:
            return False, "", str(e)

    async def restart_systemd_service(self, service_name):
        """Restart systemd service"""
        try:
            process = await asyncio.create_subprocess_exec(
                "sudo", "systemctl", "restart", f"{service_name}.service",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0, stdout.decode(), stderr.decode()
        except Exception as e:
            return False, "", str(e)