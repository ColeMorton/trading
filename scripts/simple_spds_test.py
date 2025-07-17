#!/usr/bin/env python3
"""
Simple SPDS Test

A simple test to verify the new SPDS architecture works.
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.spds_analysis_engine import SPDSAnalysisEngine, AnalysisRequest

async def main():
    """Simple test of the new architecture."""
    print("Testing new SPDS architecture...")
    
    try:
        # Test strategy analysis (simplest case)
        engine = SPDSAnalysisEngine()
        request = AnalysisRequest(
            analysis_type="strategy",
            parameter="AAPL_SMA_20_50"
        )
        
        print("Running strategy analysis...")
        results = await engine.analyze(request)
        
        print(f"✅ Success! Got {len(results)} results")
        
        # Show a sample result
        if results:
            sample_key = list(results.keys())[0]
            sample_result = results[sample_key]
            
            print(f"Sample result for {sample_key}:")
            print(f"  Exit Signal: {sample_result.exit_signal.signal_type}")
            print(f"  Confidence: {sample_result.confidence_level:.1f}%")
            print(f"  Risk Level: {sample_result.exit_signal.risk_level}")
            print(f"  Reasoning: {sample_result.exit_signal.reasoning}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())