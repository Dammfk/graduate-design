# STM32 Demo Workspace

This workspace hosts the STM32L4 demo project (Core, Drivers, KE1South) along with the Eclipse project files. The Git repository tracks source and configuration, while build artifacts are ignored.

## Structure
- `Core/`, `Drivers/`, `KE1South/`: Hand-written firmware sources and headers
- `.settings` / `.project` / `.cproject`: IDE configuration managed in source control
- `Debug/`: generated build output (ignored locally)

Run builds from the IDE or using your preferred tooling; commit only the source/configuration, not the generated binaries.
