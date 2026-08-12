import uuid
from datetime import datetime, timezone

from app.models.enums import Grade
from app.models.score import ScoreModel
from app.models.leaderboard import LeaderboardModel
from app.models.evaluation import PresentationEvaluationModel
from app.models.model_submission import ModelSubmissionModel


class TestAnalyticsOverview:
    def test_overview_no_data(self, client, organizer_headers):
        resp = client.get("/api/v1/analytics/overview", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_teams"] >= 0
        assert "average_scores" in body

    def test_overview_with_leaderboard(
        self, client, organizer_headers, db_session, team_a
    ):
        lb = LeaderboardModel(
            team_id=team_a.id,
            rank=1,
            phase1_score=50.0,
            technical_score=15.0,
            presentation_score=14.0,
            final_score=79.0,
        )
        db_session.add(lb)
        db_session.commit()

        resp = client.get("/api/v1/analytics/overview", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_teams"] >= 1
        assert body["top_team"]["team_name"] == team_a.name
        assert body["top_team"]["final_score"] == 79.0
        assert body["average_scores"]["phase1_average"] == 50.0
        assert body["average_scores"]["final_average"] == 79.0

    def test_overview_averages_multiple_teams(
        self, client, organizer_headers, db_session
    ):
        from app.models.team import TeamModel

        team_b = TeamModel(team_id="B", name="Team B", code="B", team_leader_name="Leader B")
        db_session.add(team_b)
        db_session.flush()

        for t, p1, tech, pres, final in [
            (team_a := TeamModel(team_id="A", name="Team A", code="A", team_leader_name="Leader A"),
             60.0, 20.0, 20.0, 100.0),
        ]:
            pass
        # Actually create proper data
        db_session.add(TeamModel(team_id="A", name="Team A", code="A", team_leader_name="Leader A"))
        db_session.flush()

        teams = db_session.query(TeamModel).all()
        for t in teams:
            lb = LeaderboardModel(
                team_id=t.id,
                rank=1,
                phase1_score=50.0,
                technical_score=15.0,
                presentation_score=14.0,
                final_score=79.0,
            )
            db_session.add(lb)
        db_session.commit()

        resp = client.get("/api/v1/analytics/overview", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_teams"] >= 2

    def test_overview_unauthorized(self, client):
        resp = client.get("/api/v1/analytics/overview")
        # No auth token → 401 Unauthorized (FastAPI HTTPBearer default)
        assert resp.status_code == 401


class TestAnalyticsModels:
    def test_models_no_data(self, client, organizer_headers):
        resp = client.get("/api/v1/analytics/models", headers=organizer_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_models_with_scores(
        self, client, organizer_headers, db_session, team_a, sample_match
    ):
        import uuid
        from app.models.match import MatchModel
        from datetime import datetime, timezone
        match2 = MatchModel(id=uuid.uuid4(), home_team_name="H2", away_team_name="A2", status="COMPLETED", match_number=2, scheduled_at=datetime(2026, 6, 20, 20, 0, 0, tzinfo=timezone.utc), freeze_deadline=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc), round="Group Stage")
        match3 = MatchModel(id=uuid.uuid4(), home_team_name="H3", away_team_name="A3", status="COMPLETED", match_number=3, scheduled_at=datetime(2026, 6, 20, 20, 0, 0, tzinfo=timezone.utc), freeze_deadline=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc), round="Group Stage")
        db_session.add(match2)
        db_session.add(match3)
        db_session.flush()

        scores_data = [
            ScoreModel(team_id=team_a.id, match_id=sample_match.id, winner_points=5, base_score=20.0, earned_points=20.0),
            ScoreModel(team_id=team_a.id, match_id=match2.id, winner_points=0, base_score=10.0, earned_points=5.0),
            ScoreModel(team_id=team_a.id, match_id=match3.id, winner_points=5, base_score=25.0, earned_points=25.0),
        ]
        for s in scores_data:
            db_session.add(s)
        db_session.commit()

        resp = client.get("/api/v1/analytics/models", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        entry = body[0]
        assert entry["team"] == team_a.name

        perf = entry["performance"]
        assert perf["matches_predicted"] == 3
        assert perf["accuracy_percentage"] == round((2 / 3) * 100, 1)
        assert perf["total_ai_score"] == round(20.0 + 5.0 + 25.0, 2)
        assert perf["average_match_score"] == round((20.0 + 5.0 + 25.0) / 3, 2)
        assert len(perf["ranking_trend"]) == 3

    def test_models_with_submission(
        self, client, organizer_headers, db_session, team_a, sample_match
    ):
        tid = str(team_a.id)
        mid = str(sample_match.id)

        # Add a model submission
        model = ModelSubmissionModel(
            team_id=team_a.id,
            file_name="test_model.pkl",
            file_type="pkl",
            file_path="/tmp/test.pkl",
            file_size=1024,
        )
        db_session.add(model)

        # Add a score
        db_session.add(ScoreModel(team_id=team_a.id, match_id=sample_match.id, winner_points=5, base_score=20.0))
        db_session.commit()

        resp = client.get("/api/v1/analytics/models", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        info = body[0]["model_information"]
        assert info["model_name"] == "test_model.pkl"
        assert info["file_name"] == "test_model.pkl"
        assert info["is_active"] is True


class TestAnalyticsPresentation:
    def test_presentation_no_data(self, client, organizer_headers):
        resp = client.get("/api/v1/analytics/presentation", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["teams"] == []
        assert body["criteria_rankings"] == []

    def test_presentation_with_evaluations(
        self, client, organizer_headers, db_session, team_a
    ):
        tid = team_a.id
        criteria = [
            {"name": "Problem Understanding", "max_score": 10},
            {"name": "Feature Engineering", "max_score": 15},
        ]
        judge_scores = [
            {
                "judge_id": str(uuid.uuid4()),
                "scores": {
                    "Problem Understanding": 8.0,
                    "Feature Engineering": 12.0,
                },
            },
            {
                "judge_id": str(uuid.uuid4()),
                "scores": {
                    "Problem Understanding": 7.0,
                    "Feature Engineering": 13.0,
                },
            },
        ]

        ev = PresentationEvaluationModel(
            team_id=tid,
            raw_total=20.0,
            grade=Grade.A,
            multiplier=3,
            judge_count=2,
            judge_scores=judge_scores,
            presentation_criteria_config=criteria,
            max_marks=25,
        )
        db_session.add(ev)
        db_session.commit()

        resp = client.get("/api/v1/analytics/presentation", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["teams"]) == 1
        tr = body["teams"][0]
        assert tr["team"] == team_a.name

        # Feature Engineering avg = (12+13)/2 = 12.5
        fe = [c for c in tr["criteria_averages"] if c["criterion"] == "Feature Engineering"][0]
        assert fe["avg_score"] == 12.5
        assert fe["max_score"] == 15

        # Problem Understanding avg = (8+7)/2 = 7.5
        pu = [c for c in tr["criteria_averages"] if c["criterion"] == "Problem Understanding"][0]
        assert pu["avg_score"] == 7.5
        assert pu["max_score"] == 10

        # Strongest = Feature Engineering (12.5/15 = 83.3% vs 7.5/10 = 75%)
        assert tr["strongest"]["criterion"] == "Feature Engineering"
        assert tr["weakest"]["criterion"] == "Problem Understanding"

        # Cross-team rankings
        assert len(body["criteria_rankings"]) == 2
        for cr in body["criteria_rankings"]:
            assert len(cr["rankings"]) == 1
            assert cr["best_team"] == team_a.name
            assert cr["weakest_team"] == team_a.name


class TestAnalyticsTeam:
    def test_team_not_found(self, client, organizer_headers):
        resp = client.get(
            f"/api/v1/analytics/team/{uuid.uuid4()}",
            headers=organizer_headers,
        )
        assert resp.status_code == 404

    def test_team_by_uuid(
        self, client, organizer_headers, db_session, team_a, sample_match
    ):
        import uuid
        from app.models.match import MatchModel
        from datetime import datetime, timezone
        match2 = MatchModel(id=uuid.uuid4(), home_team_name="H2", away_team_name="A2", status="COMPLETED", match_number=2, scheduled_at=datetime(2026, 6, 20, 20, 0, 0, tzinfo=timezone.utc), freeze_deadline=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc), round="Group Stage")
        db_session.add(match2)
        db_session.flush()

        scores = [
            ScoreModel(team_id=team_a.id, match_id=sample_match.id, winner_points=5, base_score=22.0),
            ScoreModel(team_id=team_a.id, match_id=match2.id, winner_points=5, base_score=18.0),
        ]
        for s in scores:
            db_session.add(s)

        lb = LeaderboardModel(
            team_id=team_a.id, rank=1, phase1_score=55.0, technical_score=18.0,
            presentation_score=16.0, final_score=89.0,
        )
        db_session.add(lb)

        criteria = [{"name": "Q&A", "max_score": 5}]
        judge_scores = [
            {"judge_id": str(uuid.uuid4()), "scores": {"Q&A": 4.0}},
        ]
        ev = PresentationEvaluationModel(
            team_id=team_a.id,
            raw_total=4.0,
            grade=Grade.A,
            multiplier=3,
            judge_count=1,
            judge_scores=judge_scores,
            presentation_criteria_config=criteria,
            max_marks=5,
        )
        db_session.add(ev)
        db_session.commit()

        resp = client.get(
            f"/api/v1/analytics/team/{team_a.id}",
            headers=organizer_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["team_name"] == team_a.name
        assert body["scores_breakdown"]["total_predictions"] == 2
        assert body["scores_breakdown"]["correct_predictions"] == 2
        assert body["leaderboard"]["rank"] == 1
        assert body["leaderboard"]["final_score"] == 89.0
        assert len(body["strengths"]) == 1
        assert body["strengths"][0]["criterion"] == "Q&A"

    def test_team_by_letter_code(
        self, client, organizer_headers, db_session, team_a
    ):
        resp = client.get(
            f"/api/v1/analytics/team/A",
            headers=organizer_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["team_name"] == team_a.name

    def test_team_leader_can_access(
        self, client, team_leader_headers, db_session, team_a
    ):
        resp = client.get(
            f"/api/v1/analytics/team/{team_a.id}",
            headers=team_leader_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["team_name"] == team_a.name
