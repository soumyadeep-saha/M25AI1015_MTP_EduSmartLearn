"""
EduSmartLearn - Safe Multi-Agent Teaching System
================================================

A protocol-first, tool-using, multi-agent teaching system implementing:
- Agent-to-Agent (A2A) Protocol for inter-agent communication
- Model Context Protocol (MCP) for standardized tool access
- Defense-in-depth safety with consent workflows
- Personalized learning through learner modeling

Usage:
    from edusmartlearn import EduSmartLearn
    
    system = EduSmartLearn()
    await system.initialize()
    response = await system.chat("Explain neural networks")

Author: Soumyadeep Saha (M25AI1015)
Project: MTech - Safe Multi-Agent Teaching System
"""

from main import EduSmartLearn

__version__ = "1.0.0"
__author__ = "Soumyadeep Saha"
__all__ = ["EduSmartLearn"]
