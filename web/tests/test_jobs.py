import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import jobs as jobs_module

def setup_function():
    jobs_module.jobs.clear()

def test_create_job_valid_type():
    job_id = jobs_module.create_job("incremental")
    assert job_id in jobs_module.jobs
    assert jobs_module.jobs[job_id]["type"] == "incremental"
    assert jobs_module.jobs[job_id]["status"] == "pending"

def test_create_job_invalid_type():
    with pytest.raises(ValueError, match="Unknown job type"):
        jobs_module.create_job("nonexistent")

def test_create_job_blocks_when_running():
    job_id = jobs_module.create_job("incremental")
    jobs_module.jobs[job_id]["status"] = "running"
    with pytest.raises(RuntimeError, match="already running"):
        jobs_module.create_job("patients")

def test_create_job_allows_after_previous_done():
    job_id = jobs_module.create_job("incremental")
    jobs_module.jobs[job_id]["status"] = "done"
    new_id = jobs_module.create_job("patients")
    assert new_id in jobs_module.jobs
