package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"rca-demo/internal/rca"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		return
	}
	command := os.Args[1]
	id := ""
	if len(os.Args) > 2 {
		id = os.Args[2]
	}
	args := []string(nil)
	if len(os.Args) > 3 {
		args = os.Args[3:]
	}
	if err := run(command, id, args); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(command, id string, args []string) error {
	switch command {
	case "create":
		incident, err := rca.NewIncident("CheckoutPaymentDependencyDegraded", "payments", "local-cli", time.Now().UTC())
		if err != nil {
			return err
		}
		if err := rca.Save(incident); err != nil {
			return err
		}
		fmt.Println(incident.ID)
		return nil
	case "status":
		return printIncident(id)
	}

	incident, err := rca.Load(id)
	if err != nil {
		return err
	}
	switch command {
	case "investigate":
		collector := rca.NewHTTPCollector(env("PROMETHEUS_URL", "http://localhost:9090"), env("LOKI_URL", "http://localhost:3100"))
		err = incident.Investigate(context.Background(), collector, "local-cli")
	case "approve-mitigation":
		err = rca.ApproveMitigation(incident, note(args), "local-cli")
	case "validate":
		err = rca.Validate(incident, "local-cli")
	case "resolve":
		err = rca.Resolve(incident, "local-cli")
	case "reinvestigate":
		err = rca.Reinvestigate(incident, "local-cli")
	case "draft-rca":
		var draft string
		draft, err = rca.DraftRCA(incident, "local-cli")
		if err == nil {
			err = rca.Save(incident)
		}
		if err == nil {
			fmt.Println(draft)
		}
		return err
	default:
		usage()
		return fmt.Errorf("unknown command: %s", command)
	}
	if err != nil {
		return err
	}
	if err := rca.Save(incident); err != nil {
		return err
	}
	return printJSON(incident)
}

func printIncident(id string) error {
	incident, err := rca.Load(id)
	if err != nil {
		return err
	}
	return printJSON(incident)
}

func printJSON(value any) error {
	payload, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	fmt.Println(string(payload))
	return nil
}

func note(args []string) string {
	for index, argument := range args {
		if argument == "--note" && index+1 < len(args) {
			return args[index+1]
		}
	}
	return "operator will validate manually"
}

func env(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: rca <create|investigate|status|approve-mitigation|validate|resolve|reinvestigate|draft-rca> [incident-id] [--note text]")
}
