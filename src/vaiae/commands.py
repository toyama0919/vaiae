#!/usr/bin/env python3
import click
import os
from .core import Core


class Mash(object):
    pass


@click.group()
@click.option(
    "--yaml-file",
    "-f",
    default=".agent-engine.yml",
    help="Path to the YAML configuration file.",
)
@click.option(
    "--profile",
    default="default",
    help="Profile name to use from YAML config.",
)
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, yaml_file, profile, debug):
    ctx.obj = Mash()
    ctx.obj.yaml_file = yaml_file
    ctx.obj.profile = profile
    ctx.obj.debug = debug

    # Initialize Core with YAML configuration
    try:
        ctx.obj.core = Core(
            yaml_file_path=yaml_file,
            profile=profile,
        )
    except Exception as e:
        click.echo(f"Error initializing Core: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--message", "-m", help="Message to send to the agent for cost analysis.")
@click.option(
    "--user-id",
    "-u",
    default=os.environ.get("USER"),
    help="User ID for the session (defaults to current user).",
)
@click.option(
    "--session-id",
    "-s",
    default=None,
    help="Session ID to continue an existing conversation.",
)
@click.option(
    "--display-name",
    "-d",
    help="Display name for the agent engine (defaults to AGENT_DISPLAY_NAME env var).",
)
@click.pass_context
def send(ctx, message, user_id, session_id, display_name):
    try:
        ctx.obj.core.send_message(
            message=message,
            display_name=display_name,
            session_id=session_id,
            user_id=user_id,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--dry-run", is_flag=True, default=False, help="Run the deployment in dry run mode."
)
@click.pass_context
def deploy(ctx, dry_run):
    """Deploy or update an agent engine from YAML configuration."""
    try:
        # Deploy using cached configuration from initialization
        ctx.obj.core.create_or_update_from_yaml(
            dry_run=dry_run,
        )

        if dry_run:
            click.echo(f"Dry run completed for profile '{ctx.obj.profile}'")
        else:
            click.echo(f"Successfully deployed agent engine using profile '{ctx.obj.profile}'")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def list(ctx):
    """List deployed agent engines from Vertex AI."""
    try:
        agent_engines = ctx.obj.core.list_agent_engine()

        if not agent_engines:
            click.echo("No agent engines found.")
            return

        click.echo(f"Found {len(agent_engines)} agent engine(s):")
        click.echo()

        for agent_engine in agent_engines:
            click.echo(f"Display Name: {agent_engine.display_name}")
            click.echo(f"Resource Name: {agent_engine.resource_name}")
            click.echo(f"Create Time: {getattr(agent_engine, 'create_time', 'N/A')}")
            click.echo(f"Update Time: {getattr(agent_engine, 'update_time', 'N/A')}")
            click.echo("-" * 50)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--name",
    "-n",
    help="Display name of the agent engine to delete.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force delete the agent engine and its child resources.",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Run the deletion in dry run mode."
)
@click.pass_context
def delete(ctx, name, force, dry_run):
    """Delete a deployed agent engine from Vertex AI."""
    try:
        if name:
            # Delete using display name
            ctx.obj.core.delete_agent_engine(
                name=name,
                force=force,
                dry_run=dry_run,
            )
            if dry_run:
                click.echo(f"Dry run completed for '{name}' deletion")
            else:
                click.echo(f"Successfully deleted agent engine '{name}'")
        else:
            # Delete using current profile configuration
            ctx.obj.core.delete_agent_engine_from_yaml(
                force=force,
                dry_run=dry_run,
            )
            if dry_run:
                click.echo(f"Dry run completed for profile '{ctx.obj.profile}' deletion")
            else:
                click.echo(f"Successfully deleted agent engine using profile '{ctx.obj.profile}'")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def main():
    cli(obj={})
