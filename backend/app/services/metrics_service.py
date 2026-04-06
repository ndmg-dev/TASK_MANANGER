from datetime import datetime, timedelta, timezone
from app.extensions import get_supabase


class MetricsService:
    """Service for computing Kanban metrics from event log."""

    @staticmethod
    def get_throughput(weeks=12):
        """Tickets moved to Done per week for the last N weeks."""
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(weeks=weeks)

        # Get current Done tickets to ensure we only count tickets that are ACTUALLY Done
        current_done_req = sb.table("tickets").select("id").eq("status", "Done").execute()
        current_done_ids = {t["id"] for t in (current_done_req.data or [])}

        if not current_done_ids:
            # Se não houver tickets em 'Done', reflete 0.
            result_data = []
            for i in range(weeks):
                week_date = start_date + timedelta(weeks=i)
                result_data.append({
                    "week": week_date.strftime("%Y-W%W"),
                    "label": week_date.strftime("%d/%m"),
                    "count": 0
                })
            return result_data

        result = sb.table("ticket_events_log").select("*").eq(
            "status_novo", "Done"
        ).gte("timestamp", start_date.isoformat()).execute()

        events = result.data or []

        # Pega apenas o último evento 'Done' de cada ticket que AINDA está Done
        last_done = {}
        for event in events:
            tid = event["ticket_id"]
            if tid not in current_done_ids:
                continue
            ts = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            if tid not in last_done or ts > last_done[tid]:
                last_done[tid] = ts

        # Group by ISO week
        weekly = {}
        for tid, ts in last_done.items():
            week_key = ts.strftime("%Y-W%W")
            week_label = ts.strftime("%d/%m")
            if week_key not in weekly:
                weekly[week_key] = {"week": week_key, "label": week_label, "count": 0}
            weekly[week_key]["count"] += 1

        # Fill missing weeks
        result_data = []
        for i in range(weeks):
            week_date = start_date + timedelta(weeks=i)
            week_key = week_date.strftime("%Y-W%W")
            week_label = week_date.strftime("%d/%m")
            if week_key in weekly:
                result_data.append(weekly[week_key])
            else:
                result_data.append({"week": week_key, "label": week_label, "count": 0})

        return result_data

    @staticmethod
    def get_cycle_time():
        """Average time from 'In Progress' to 'Done' in hours."""
        sb = get_supabase()

        current_done_req = sb.table("tickets").select("id").eq("status", "Done").execute()
        current_done_ids = {t["id"] for t in (current_done_req.data or [])}

        if not current_done_ids:
            return {"average_hours": 0, "average_days": 0, "total_tickets": 0, "details": []}

        # Get all 'In Progress' events
        in_progress = sb.table("ticket_events_log").select(
            "ticket_id, timestamp"
        ).eq("status_novo", "In Progress").execute()

        # Get all 'Done' events
        done = sb.table("ticket_events_log").select(
            "ticket_id, timestamp"
        ).eq("status_novo", "Done").execute()

        ip_map = {}
        for ev in (in_progress.data or []):
            tid = ev["ticket_id"]
            if tid not in current_done_ids:
                continue
            ts = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
            if tid not in ip_map or ts < ip_map[tid]:
                ip_map[tid] = ts  # First time entering In Progress

        done_map = {}
        for ev in (done.data or []):
            tid = ev["ticket_id"]
            if tid not in current_done_ids:
                continue
            ts = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
            if tid not in done_map or ts > done_map[tid]:
                done_map[tid] = ts # Last time entering Done

        cycle_times = []
        for tid, done_ts in done_map.items():
            if tid in ip_map:
                delta = (done_ts - ip_map[tid]).total_seconds() / 3600  # hours
                if delta > 0:
                    cycle_times.append({"ticket_id": tid, "hours": round(delta, 2)})

        avg = round(sum(ct["hours"] for ct in cycle_times) / len(cycle_times), 2) if cycle_times else 0
        avg_days = round(avg / 24, 1)

        return {
            "average_hours": avg,
            "average_days": avg_days,
            "total_tickets": len(cycle_times),
            "details": cycle_times[-20:],  # Last 20 for chart
        }

    @staticmethod
    def get_lead_time():
        """Average time from ticket creation (Backlog) to Done in hours."""
        sb = get_supabase()

        current_done_req = sb.table("tickets").select("id").eq("status", "Done").execute()
        current_done_ids = {t["id"] for t in (current_done_req.data or [])}

        if not current_done_ids:
             return {"average_hours": 0, "average_days": 0, "total_tickets": 0}

        # Get creation events (status_anterior is null)
        created = sb.table("ticket_events_log").select(
            "ticket_id, timestamp"
        ).is_("status_anterior", "null").execute()

        done = sb.table("ticket_events_log").select(
            "ticket_id, timestamp"
        ).eq("status_novo", "Done").execute()

        create_map = {}
        for ev in (created.data or []):
            tid = ev["ticket_id"]
            if tid not in current_done_ids:
                continue
            ts = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
            if tid not in create_map or ts < create_map[tid]:
                create_map[tid] = ts

        done_map = {}
        for ev in (done.data or []):
            tid = ev["ticket_id"]
            if tid not in current_done_ids:
                continue
            ts = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
            if tid not in done_map or ts > done_map[tid]:
                done_map[tid] = ts

        lead_times = []
        for tid, done_ts in done_map.items():
            if tid in create_map:
                delta = (done_ts - create_map[tid]).total_seconds() / 3600
                if delta > 0:
                    lead_times.append({"ticket_id": tid, "hours": round(delta, 2)})

        avg = round(sum(lt["hours"] for lt in lead_times) / len(lead_times), 2) if lead_times else 0
        avg_days = round(avg / 24, 1)

        return {
            "average_hours": avg,
            "average_days": avg_days,
            "total_tickets": len(lead_times),
        }

    @staticmethod
    def get_bottlenecks():
        """Identify bottlenecks: columns with >5 tickets and tickets stalled >48h."""
        sb = get_supabase()
        now = datetime.now(timezone.utc)

        # Current ticket counts per column (exclude Done)
        tickets = sb.table("tickets").select(
            "id, titulo, status, updated_at, assignee:users!assignee_id(full_name)"
        ).neq("status", "Done").execute()

        all_tickets = tickets.data or []

        # Count per column
        column_counts = {}
        for t in all_tickets:
            status = t["status"]
            column_counts[status] = column_counts.get(status, 0) + 1

        # WIP violations (>5)
        wip_violations = [
            {"column": col, "count": count}
            for col, count in column_counts.items() if count > 5
        ]

        # Stalled tickets (>48h without status change)
        stalled = []
        for t in all_tickets:
            updated = datetime.fromisoformat(t["updated_at"].replace("Z", "+00:00"))
            hours_stalled = (now - updated).total_seconds() / 3600
            if hours_stalled > 48:
                stalled.append({
                    "ticket_id": t["id"],
                    "titulo": t["titulo"],
                    "status": t["status"],
                    "hours_stalled": round(hours_stalled, 1),
                    "assignee": t.get("assignee", {}).get("full_name") if t.get("assignee") else None,
                })

        return {
            "wip_violations": wip_violations,
            "stalled_tickets": stalled,
            "column_counts": column_counts,
        }
