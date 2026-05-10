"""Application entry point.

Boots a QApplication, initializes the application controller, and enters
 the Qt event loop.
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from app import ApplicationController


def main() -> None:
    """Run the Job Hunter Desktop App."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Job Hunter")
    app.setOrganizationName("job-hunter")

    from widgets.theme import QuantumTheme
    QuantumTheme.apply(app)

    controller = ApplicationController()
    controller.run()

    # Graceful shutdown on Qt quit
    app.aboutToQuit.connect(controller.shutdown)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
