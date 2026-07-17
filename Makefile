.PHONY: help bootstrap install services-install portal gateway-operator gateway-app gateway-game gateway-creative dashboard-operator snapshot configure-postgres seed-memory memory-summary seed-cognition cognition-summary activate-cognition detect-contradictions dream-cycle experiment-cycle council write-reflection create-project update-project orchestrate

help:
	@echo "Hermes Standalone Stack"
	@echo "Targets:"
	@echo "  make bootstrap         - generate standalone Hermes profile homes"
	@echo "  make install           - install Hermes into state/hermes/venv"
	@echo "  make services-install  - install always-on user services plus the watchdog timer"
	@echo "  make portal            - run the operator portal"
	@echo "  make gateway-operator  - run the operator gateway"
	@echo "  make gateway-app       - run the app-dev gateway"
	@echo "  make gateway-game      - run the game-dev gateway"
	@echo "  make gateway-creative  - run the creative-dev gateway"
	@echo "  make dashboard-operator - run the operator dashboard"
	@echo "  make snapshot          - print current runtime snapshot"
	@echo "  make configure-postgres - switch Hermes control-plane state to Postgres"
	@echo "  make seed-memory       - seed agent memory graph into the active backend"
	@echo "  make memory-summary PROFILE=sheldon - inspect agent memory graph"
	@echo "  make seed-cognition    - seed the cognitive kernel"
	@echo "  make cognition-summary - inspect cognitive kernel state"
	@echo "  make activate-cognition QUERY='...' PROFILE=sheldon - activate memory/facts/procedures"
	@echo "  make dream-cycle       - run idle cognition jobs"
	@echo "  make experiment-cycle  - propose autonomous project experiments"
	@echo "  make council TOPIC='...' - run agent council deliberation"
	@echo "  make create-project PROJECT_ID=id TITLE='Title' - scaffold a persistent project"
	@echo "  make update-project PROJECT_ID=id NOW='...' NEXT='...' - update persistent project tracking"
	@echo "  make orchestrate PROJECT_ID=id OBJECTIVE='...' - run the lead -> creative -> game -> app pipeline"

bootstrap:
	@./scripts/bootstrap-hermes.sh

install:
	@./scripts/install-hermes.sh

services-install:
	@./scripts/install-hermes-services.sh

portal:
	@./scripts/run-operator-portal.sh

gateway-operator:
	@./scripts/run-hermes-gateway.sh operator

gateway-app:
	@./scripts/run-hermes-gateway.sh app-dev

gateway-game:
	@./scripts/run-hermes-gateway.sh game-dev

gateway-creative:
	@./scripts/run-hermes-gateway.sh creative-dev

dashboard-operator:
	@./scripts/run-hermes-dashboard.sh operator

snapshot:
	@python3 -m hermes_stack.scaffold --root-dir . snapshot

configure-postgres:
	@python3 -m hermes_stack.scaffold --root-dir . --database-url "$(DATABASE_URL)" configure-postgres

seed-memory:
	@python3 -m hermes_stack.scaffold --root-dir . seed-memory

memory-summary:
	@python3 -m hermes_stack.scaffold --root-dir . --profile "$(PROFILE)" memory-summary

seed-cognition:
	@python3 -m hermes_stack.scaffold --root-dir . seed-cognition

cognition-summary:
	@python3 -m hermes_stack.scaffold --root-dir . cognition-summary

activate-cognition:
	@python3 -m hermes_stack.scaffold --root-dir . --profile "$(PROFILE)" --project-id "$(PROJECT_ID)" --query "$(QUERY)" activate-cognition

detect-contradictions:
	@python3 -m hermes_stack.scaffold --root-dir . detect-contradictions

dream-cycle:
	@python3 -m hermes_stack.scaffold --root-dir . dream-cycle

experiment-cycle:
	@python3 -m hermes_stack.scaffold --root-dir . experiment-cycle

council:
	@python3 -m hermes_stack.scaffold --root-dir . --project-id "$(PROJECT_ID)" --topic "$(TOPIC)" council

write-reflection:
	@python3 -m hermes_stack.scaffold --root-dir . --profile "$(PROFILE)" --project-id "$(PROJECT_ID)" --title "$(TITLE)" --content "$(CONTENT)" write-reflection

create-project:
	@python3 -m hermes_stack.scaffold --root-dir . create-project --project-id "$(PROJECT_ID)" --title "$(TITLE)" --summary "$(SUMMARY)" --specialists "$(SPECIALISTS)"

update-project:
	@python3 -m hermes_stack.scaffold --root-dir . update-project --project-id "$(PROJECT_ID)" $(if $(TITLE),--title "$(TITLE)") $(if $(SUMMARY),--summary "$(SUMMARY)") $(if $(SPECIALISTS),--specialists "$(SPECIALISTS)") $(if $(STATUS),--status "$(STATUS)") $(if $(OWNER),--owner "$(OWNER)") $(if $(NOW),--now "$(NOW)") $(if $(NEXT),--next "$(NEXT)") $(foreach item,$(BLOCKED),--blocked "$(item)") $(foreach item,$(DONE),--done "$(item)") $(if $(PERCENT),--percent "$(PERCENT)") $(if $(PRIORITY),--priority "$(PRIORITY)")

orchestrate:
	@python3 ./scripts/hermes-orchestrate-pipeline.py --root-dir . --project-id "$(PROJECT_ID)" --objective "$(OBJECTIVE)" $(if $(TIMEOUT),--timeout "$(TIMEOUT)")
