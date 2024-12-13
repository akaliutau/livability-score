# Check if the required environment variable is set
if [[ -z "${OPENWEATHER_API_KEY:-}" ]]; then
  echo "Error: Environment variable 'OPENWEATHER_API_KEY' is not set. Signup at https://openweathermap.org/api/ and get the api key" >&2
  return 1  # Return with an error status
fi
export PROJECT_ID=dev-iot-application
export HOME_ID=1
export IS_LOCAL_ENV=true
