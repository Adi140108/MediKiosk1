/**
 * MediKiosk Patient Intake App Entrypoint
 */
document.addEventListener("DOMContentLoaded", () => {
  if (typeof PatientIntake !== "undefined") {
    PatientIntake.init();
  }
});
